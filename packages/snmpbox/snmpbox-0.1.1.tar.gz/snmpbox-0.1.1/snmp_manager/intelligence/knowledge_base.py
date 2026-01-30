"""
Knowledge Base - Crowdsourced device profile database.

This module manages a community-driven knowledge base of device profiles,
OID mappings, and best practices for various telecom equipment.
"""

import asyncio
import json
import logging
import hashlib
import time
from typing import Dict, List, Set, Optional, Tuple, Any, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
import re
from collections import defaultdict

from .oid_explorer import OIDNode
from .reverse_engineer import ReverseEngineeringResult

logger = logging.getLogger(__name__)


@dataclass
class DeviceProfile:
    """Device profile contributed by the community."""
    profile_id: str
    vendor: str
    device_type: str
    model: str
    firmware_versions: List[str] = field(default_factory=list)
    contributed_by: str = "anonymous"
    contribution_date: float = field(default_factory=time.time)
    verified: bool = False
    verification_count: int = 0
    rating: float = 0.0
    total_ratings: int = 0
    tags: List[str] = field(default_factory=list)
    oid_mappings: Dict[str, str] = field(default_factory=dict)  # friendly_name -> oid
    working_oids: List[str] = field(default_factory=list)
    problematic_oids: List[str] = field(default_factory=list)
    access_patterns: Dict[str, Any] = field(default_factory=dict)  # community, version, etc.
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Contribution:
    """Represents a community contribution."""
    contribution_id: str
    contributor: str
    device_signature: Dict[str, Any]
    discovered_data: Dict[str, Any]
    confidence_score: float
    timestamp: float
    verified: bool = False
    comments: str = ""


@dataclass
class SimilarityMatch:
    """Result of similarity matching."""
    profile_id: str
    similarity_score: float
    matching_oids: List[str]
    missing_oids: List[str]
    additional_oids: List[str]
    confidence_explanation: str


class KnowledgeBase:
    """
    Community-driven knowledge base for device profiles.

    Features:
    - Store and retrieve device profiles
    - Similarity matching for unknown devices
    - Community verification and rating system
    - Automatic profile quality assessment
    - Profile merging and conflict resolution
    - Export/import capabilities
    """

    def __init__(self, data_dir: str = "knowledge_base"):
        """
        Initialize knowledge base.

        Args:
            data_dir: Directory to store knowledge base data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # Storage
        self.profiles: Dict[str, DeviceProfile] = {}
        self.contributions: Dict[str, Contribution] = {}
        self.similarity_cache: Dict[str, List[SimilarityMatch]] = {}
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)  # tag -> profile_ids

        # Statistics
        self.stats = {
            "total_profiles": 0,
            "verified_profiles": 0,
            "total_contributions": 0,
            "vendors_count": 0,
            "device_types_count": 0,
            "last_updated": time.time()
        }

        # Load existing data
        self._load_profiles()
        self._update_statistics()

    def add_device_profile(
        self,
        profile: DeviceProfile,
        auto_verify: bool = False
    ) -> str:
        """
        Add a device profile to the knowledge base.

        Args:
            profile: Device profile to add
            auto_verify: Whether to auto-verify high-quality profiles

        Returns:
            Profile ID
        """
        # Generate profile ID if not provided
        if not profile.profile_id:
            profile.profile_id = self._generate_profile_id(profile)

        # Quality assessment
        quality_score = self._assess_profile_quality(profile)

        # Auto-verify high-quality profiles
        if auto_verify and quality_score > 0.8:
            profile.verified = True
            logger.info(f"Auto-verified high-quality profile: {profile.profile_id}")

        # Check for existing similar profiles
        similar_profiles = self.find_similar_profiles(profile, threshold=0.7)

        if similar_profiles:
            logger.info(f"Found {len(similar_profiles)} similar profiles for {profile.profile_id}")
            # Could merge or flag for review here

        # Add to storage
        self.profiles[profile.profile_id] = profile

        # Update tag index
        for tag in profile.tags:
            self.tag_index[tag].add(profile.profile_id)

        # Save to disk
        self._save_profile(profile)

        # Update statistics
        self._update_statistics()

        logger.info(f"Added device profile: {profile.profile_id}")
        return profile.profile_id

    def add_contribution(self, contribution: Contribution) -> str:
        """
        Add a community contribution.

        Args:
            contribution: Contribution to add

        Returns:
            Contribution ID
        """
        if not contribution.contribution_id:
            contribution.contribution_id = self._generate_contribution_id(contribution)

        self.contributions[contribution.contribution_id] = contribution
        self._save_contribution(contribution)

        # Try to create a profile from this contribution
        if contribution.confidence_score > 0.6:
            self._create_profile_from_contribution(contribution)

        self.stats["total_contributions"] += 1
        logger.info(f"Added contribution: {contribution.contribution_id}")

        return contribution.contribution_id

    def get_profile(self, profile_id: str) -> Optional[DeviceProfile]:
        """Get a device profile by ID."""
        return self.profiles.get(profile_id)

    def search_profiles(
        self,
        vendor: str = None,
        device_type: str = None,
        model: str = None,
        tags: List[str] = None,
        verified_only: bool = False,
        min_rating: float = 0.0
    ) -> List[DeviceProfile]:
        """
        Search device profiles with various criteria.

        Args:
            vendor: Filter by vendor
            device_type: Filter by device type
            model: Filter by model (partial match)
            tags: Filter by tags (must match all)
            verified_only: Only return verified profiles
            min_rating: Minimum rating threshold

        Returns:
            List of matching profiles
        """
        results = []

        for profile in self.profiles.values():
            # Vendor filter
            if vendor and profile.vendor.lower() != vendor.lower():
                continue

            # Device type filter
            if device_type and profile.device_type.lower() != device_type.lower():
                continue

            # Model filter
            if model and model.lower() not in profile.model.lower():
                continue

            # Tags filter
            if tags and not all(tag in profile.tags for tag in tags):
                continue

            # Verification filter
            if verified_only and not profile.verified:
                continue

            # Rating filter
            if profile.rating < min_rating:
                continue

            results.append(profile)

        # Sort by rating and verification status
        results.sort(key=lambda p: (p.verified, p.rating), reverse=True)
        return results

    def find_similar_profiles(
        self,
        target_profile: DeviceProfile,
        threshold: float = 0.5,
        max_results: int = 10
    ) -> List[SimilarityMatch]:
        """
        Find profiles similar to a target profile.

        Args:
            target_profile: Profile to find matches for
            threshold: Minimum similarity threshold
            max_results: Maximum number of results

        Returns:
            List of similarity matches
        """
        cache_key = self._generate_cache_key(target_profile)
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key][:max_results]

        matches = []

        for profile_id, profile in self.profiles.items():
            if profile_id == target_profile.profile_id:
                continue

            similarity = self._calculate_profile_similarity(target_profile, profile)

            if similarity >= threshold:
                matches.append(SimilarityMatch(
                    profile_id=profile_id,
                    similarity_score=similarity,
                    matching_oids=self._find_matching_oids(target_profile, profile),
                    missing_oids=self._find_missing_oids(target_profile, profile),
                    additional_oids=self._find_additional_oids(target_profile, profile),
                    confidence_explanation=self._explain_similarity(target_profile, profile, similarity)
                ))

        # Sort by similarity score
        matches.sort(key=lambda m: m.similarity_score, reverse=True)

        # Cache results
        self.similarity_cache[cache_key] = matches

        return matches[:max_results]

    def get_profile_for_device(
        self,
        device_signature: Dict[str, Any],
        discovered_oids: List[str],
        vendor_hint: str = None
    ) -> Optional[DeviceProfile]:
        """
        Get the best matching profile for a device.

        Args:
            device_signature: Device signature from fingerprinting
            discovered_oids: List of discovered OIDs
            vendor_hint: Optional vendor hint

        Returns:
            Best matching profile or None
        """
        # Search by vendor and device type first
        vendor = device_signature.get("vendor") or vendor_hint
        device_type = device_signature.get("device_type")

        if vendor and device_type:
            candidates = self.search_profiles(
                vendor=vendor,
                device_type=device_type,
                verified_only=True
            )

            if candidates:
                # Find best match based on OID overlap
                best_match = None
                best_score = 0.0

                for profile in candidates:
                    oid_overlap = len(set(discovered_oids) & set(profile.working_oids))
                    score = oid_overlap / max(len(discovered_oids), len(profile.working_oids))

                    if score > best_score:
                        best_score = score
                        best_match = profile

                if best_score > 0.3:  # Minimum threshold
                    logger.info(f"Found matching profile {best_match.profile_id} with score {best_score:.2f}")
                    return best_match

        # Fallback to similarity search
        temp_profile = DeviceProfile(
            profile_id="temp",
            vendor=vendor or "unknown",
            device_type=device_type or "unknown",
            model="unknown",
            working_oids=discovered_oids
        )

        similar = self.find_similar_profiles(temp_profile, threshold=0.3)

        if similar:
            best_profile = self.profiles.get(similar[0].profile_id)
            logger.info(f"Found similar profile {best_profile.profile_id} with similarity {similar[0].similarity_score:.2f}")
            return best_profile

        return None

    def update_profile_rating(self, profile_id: str, rating: int, user: str = "anonymous"):
        """
        Update a profile's rating.

        Args:
            profile_id: Profile ID to rate
            rating: Rating (1-5)
            user: User providing rating
        """
        profile = self.profiles.get(profile_id)
        if not profile:
            return False

        # Update rating (simple average)
        total_rating = profile.rating * profile.total_ratings + rating
        profile.total_ratings += 1
        profile.rating = total_rating / profile.total_ratings

        self._save_profile(profile)
        logger.info(f"Updated rating for {profile_id}: {profile.rating:.2f} ({profile.total_ratings} ratings)")
        return True

    def verify_profile(self, profile_id: str, verifier: str = "community"):
        """Verify a profile as working correctly."""
        profile = self.profiles.get(profile_id)
        if not profile:
            return False

        profile.verified = True
        profile.verification_count += 1
        profile.metadata["verified_by"] = verifier
        profile.metadata["verified_date"] = time.time()

        self._save_profile(profile)
        logger.info(f"Verified profile: {profile_id}")
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        return self.stats.copy()

    def export_profiles(
        self,
        output_file: str,
        vendor: str = None,
        verified_only: bool = True
    ):
        """
        Export profiles to a file.

        Args:
            output_file: Output file path
            vendor: Filter by vendor (optional)
            verified_only: Only export verified profiles
        """
        profiles_to_export = []

        for profile in self.profiles.values():
            if verified_only and not profile.verified:
                continue
            if vendor and profile.vendor.lower() != vendor.lower():
                continue
            profiles_to_export.append(profile)

        export_data = {
            "export_date": time.time(),
            "total_profiles": len(profiles_to_export),
            "filter": {"vendor": vendor, "verified_only": verified_only},
            "profiles": [asdict(profile) for profile in profiles_to_export]
        }

        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported {len(profiles_to_export)} profiles to {output_file}")

    def import_profiles(self, input_file: str, merge_strategy: str = "skip"):
        """
        Import profiles from a file.

        Args:
            input_file: Input file path
            merge_strategy: How to handle conflicts ("skip", "overwrite", "merge")
        """
        with open(input_file, 'r') as f:
            import_data = json.load(f)

        imported_count = 0
        skipped_count = 0

        for profile_data in import_data.get("profiles", []):
            profile = DeviceProfile(**profile_data)

            if profile.profile_id in self.profiles:
                if merge_strategy == "skip":
                    skipped_count += 1
                    continue
                elif merge_strategy == "merge":
                    # Merge profiles (combine OIDs, etc.)
                    existing = self.profiles[profile.profile_id]
                    profile.working_oids = list(set(existing.working_oids + profile.working_oids))
                    profile.rating = (existing.rating + profile.rating) / 2

            self.add_device_profile(profile)
            imported_count += 1

        logger.info(f"Imported {imported_count} profiles, skipped {skipped_count} from {input_file}")

    def _load_profiles(self):
        """Load existing profiles from disk."""
        profiles_dir = self.data_dir / "profiles"
        if not profiles_dir.exists():
            return

        for profile_file in profiles_dir.glob("*.json"):
            try:
                with open(profile_file, 'r') as f:
                    profile_data = json.load(f)
                    profile = DeviceProfile(**profile_data)
                    self.profiles[profile.profile_id] = profile

                    # Update tag index
                    for tag in profile.tags:
                        self.tag_index[tag].add(profile.profile_id)

            except Exception as e:
                logger.error(f"Failed to load profile {profile_file}: {e}")

        logger.info(f"Loaded {len(self.profiles)} profiles from disk")

    def _save_profile(self, profile: DeviceProfile):
        """Save a profile to disk."""
        profiles_dir = self.data_dir / "profiles"
        profiles_dir.mkdir(exist_ok=True)

        profile_file = profiles_dir / f"{profile.profile_id}.json"
        with open(profile_file, 'w') as f:
            json.dump(asdict(profile), f, indent=2)

    def _save_contribution(self, contribution: Contribution):
        """Save a contribution to disk."""
        contributions_dir = self.data_dir / "contributions"
        contributions_dir.mkdir(exist_ok=True)

        contribution_file = contributions_dir / f"{contribution.contribution_id}.json"
        with open(contribution_file, 'w') as f:
            json.dump(asdict(contribution), f, indent=2, default=str)

    def _generate_profile_id(self, profile: DeviceProfile) -> str:
        """Generate a unique profile ID."""
        content = f"{profile.vendor}_{profile.device_type}_{profile.model}_{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _generate_contribution_id(self, contribution: Contribution) -> str:
        """Generate a unique contribution ID."""
        content = f"{contribution.contributor}_{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _generate_cache_key(self, profile: DeviceProfile) -> str:
        """Generate cache key for similarity searches."""
        content = f"{profile.vendor}_{profile.device_type}_{len(profile.working_oids)}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _assess_profile_quality(self, profile: DeviceProfile) -> float:
        """Assess the quality of a profile (0.0 to 1.0)."""
        score = 0.0

        # OID coverage (0.3 weight)
        if len(profile.working_oids) > 20:
            score += 0.3
        elif len(profile.working_oids) > 10:
            score += 0.2
        elif len(profile.working_oids) > 5:
            score += 0.1

        # Friendly name mappings (0.2 weight)
        if len(profile.oid_mappings) > 15:
            score += 0.2
        elif len(profile.oid_mappings) > 8:
            score += 0.15
        elif len(profile.oid_mappings) > 3:
            score += 0.1

        # Documentation quality (0.2 weight)
        if len(profile.notes) > 100:
            score += 0.2
        elif len(profile.notes) > 50:
            score += 0.15
        elif len(profile.notes) > 20:
            score += 0.1

        # Performance metrics (0.1 weight)
        if profile.performance_metrics:
            score += 0.1

        # Tag coverage (0.1 weight)
        if len(profile.tags) > 5:
            score += 0.1
        elif len(profile.tags) > 2:
            score += 0.05

        # Access patterns (0.1 weight)
        if profile.access_patterns:
            score += 0.1

        return min(score, 1.0)

    def _calculate_profile_similarity(self, profile1: DeviceProfile, profile2: DeviceProfile) -> float:
        """Calculate similarity between two profiles."""
        similarity = 0.0

        # Vendor match (0.3 weight)
        if profile1.vendor.lower() == profile2.vendor.lower():
            similarity += 0.3

        # Device type match (0.2 weight)
        if profile1.device_type.lower() == profile2.device_type.lower():
            similarity += 0.2

        # Model similarity (0.2 weight)
        model_similarity = self._calculate_string_similarity(profile1.model, profile2.model)
        similarity += model_similarity * 0.2

        # OID overlap (0.3 weight)
        oid_overlap = len(set(profile1.working_oids) & set(profile2.working_oids))
        oid_union = len(set(profile1.working_oids) | set(profile2.working_oids))
        if oid_union > 0:
            similarity += (oid_overlap / oid_union) * 0.3

        return similarity

    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings."""
        str1_lower = str1.lower()
        str2_lower = str2.lower()

        # Exact match
        if str1_lower == str2_lower:
            return 1.0

        # Contains match
        if str1_lower in str2_lower or str2_lower in str1_lower:
            return 0.8

        # Word overlap
        words1 = set(str1_lower.split())
        words2 = set(str2_lower.split())

        if words1 and words2:
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            return intersection / union

        return 0.0

    def _find_matching_oids(self, profile1: DeviceProfile, profile2: DeviceProfile) -> List[str]:
        """Find OIDs that match between two profiles."""
        return list(set(profile1.working_oids) & set(profile2.working_oids))

    def _find_missing_oids(self, profile1: DeviceProfile, profile2: DeviceProfile) -> List[str]:
        """Find OIDs that are in profile2 but missing from profile1."""
        return list(set(profile2.working_oids) - set(profile1.working_oids))

    def _find_additional_oids(self, profile1: DeviceProfile, profile2: DeviceProfile) -> List[str]:
        """Find OIDs that are in profile1 but missing from profile2."""
        return list(set(profile1.working_oids) - set(profile2.working_oids))

    def _explain_similarity(
        self,
        profile1: DeviceProfile,
        profile2: DeviceProfile,
        similarity: float
    ) -> str:
        """Generate explanation for similarity score."""
        reasons = []

        if profile1.vendor.lower() == profile2.vendor.lower():
            reasons.append("Same vendor")

        if profile1.device_type.lower() == profile2.device_type.lower():
            reasons.append("Same device type")

        oid_overlap = len(set(profile1.working_oids) & set(profile2.working_oids))
        if oid_overlap > 0:
            reasons.append(f"{oid_overlap} shared OIDs")

        model_sim = self._calculate_string_similarity(profile1.model, profile2.model)
        if model_sim > 0.5:
            reasons.append("Similar model names")

        return "; ".join(reasons) if reasons else "General similarity"

    def _create_profile_from_contribution(self, contribution: Contribution):
        """Create a device profile from a contribution."""
        device_sig = contribution.device_signature
        discovered_data = contribution.discovered_data

        profile = DeviceProfile(
            profile_id="",  # Will be generated
            vendor=device_sig.get("vendor", "unknown"),
            device_type=device_sig.get("device_type", "unknown"),
            model=device_sig.get("model", "unknown"),
            contributed_by=contribution.contributor,
            confidence_score=contribution.confidence_score,
            working_oids=list(discovered_data.keys()),
            tags=["auto-generated", "from-contribution"]
        )

        self.add_device_profile(profile)

    def _update_statistics(self):
        """Update knowledge base statistics."""
        self.stats["total_profiles"] = len(self.profiles)
        self.stats["verified_profiles"] = len([p for p in self.profiles.values() if p.verified])
        self.stats["vendors_count"] = len(set(p.vendor for p in self.profiles.values()))
        self.stats["device_types_count"] = len(set(p.device_type for p in self.profiles.values()))
        self.stats["last_updated"] = time.time()