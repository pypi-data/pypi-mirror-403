from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Tuple
from pathlib import PurePath
from geopic_tag_reader.reader import GeoPicTags
import datetime
from rtree import index
import math


class SortMethod(str, Enum):
    filename_asc = "filename-asc"
    filename_desc = "filename-desc"
    time_asc = "time-asc"
    time_desc = "time-desc"


@dataclass
class MergeParams:
    maxDistance: Optional[float] = None
    maxRotationAngle: Optional[int] = None

    def is_merge_needed(self):
        # Only check max distance, as max rotation angle is only useful when dist is defined
        return self.maxDistance is not None


@dataclass
class SplitParams:
    maxDistance: Optional[int] = None
    maxTime: Optional[int] = None

    def is_split_needed(self):
        return self.maxDistance is not None or self.maxTime is not None


@dataclass
class Picture:
    filename: str
    metadata: GeoPicTags
    heading_computed: bool = False

    def distance_to(self, other) -> float:
        """Computes distance in meters based on Haversine formula"""
        R = 6371000
        phi1 = math.radians(self.metadata.lat)
        phi2 = math.radians(other.metadata.lat)
        delta_phi = math.radians(other.metadata.lat - self.metadata.lat)
        delta_lambda = math.radians(other.metadata.lon - self.metadata.lon)
        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        return distance

    def rotation_angle(self, other) -> Optional[int]:
        return rotation_angle(self.metadata.heading, other.metadata.heading)


def rotation_angle(heading1: Optional[int], heading2: Optional[int]) -> Optional[int]:
    """Computes relative heading between two headings

    >>> rotation_angle(120, 120)
    0
    >>> rotation_angle(120, 240)
    120
    >>> rotation_angle(15, 335)
    40
    >>> rotation_angle(335, 15)
    40
    >>> rotation_angle(None, 15)

    """
    if heading1 is None or heading2 is None:
        return None
    diff = (heading1 - heading2) % 360
    return min(diff, 360 - diff)


class SplitReason(str, Enum):
    time = "time"
    distance = "distance"


@dataclass
class Split:
    prevPic: Picture
    nextPic: Picture
    reason: SplitReason


@dataclass
class Sequence:
    pictures: List[Picture]

    def from_ts(self) -> Optional[datetime.datetime]:
        """Start date/time of this sequence"""

        if len(self.pictures) == 0:
            return None
        return self.pictures[0].metadata.ts

    def to_ts(self) -> Optional[datetime.datetime]:
        """End date/time of this sequence"""

        if len(self.pictures) == 0:
            return None
        return self.pictures[-1].metadata.ts

    def delta_with(self, otherSeq) -> Optional[Tuple[datetime.timedelta, float]]:
        """
        Delta between the end of this sequence and the start of the other one.
        Returns a tuple (timedelta, distance in meters)
        """

        if len(self.pictures) == 0 or len(otherSeq.pictures) == 0:
            return None

        return (otherSeq.from_ts() - self.to_ts(), otherSeq.pictures[0].distance_to(self.pictures[-1]))  # type: ignore


@dataclass
class Duplicate:
    picture: Picture
    duplicate_of: Picture
    distance: float
    angle: Optional[int]


@dataclass
class DispatchReport:
    sequences: List[Sequence]
    duplicate_pictures: List[Duplicate] = field(default_factory=list)
    sequences_splits: List[Split] = field(default_factory=list)


def sort_pictures(pictures: List[Picture], method: Optional[SortMethod] = SortMethod.time_asc) -> List[Picture]:
    """Sorts pictures according to given strategy

    Parameters
    ----------
    pictures : Picture[]
        List of pictures to sort
    method : SortMethod
        Sort logic to adopt (time-asc, time-desc, filename-asc, filename-desc)

    Returns
    -------
    Picture[]
        List of pictures, sorted
    """

    if method is None:
        method = SortMethod.time_asc

    if method not in [item.value for item in SortMethod]:
        raise Exception("Invalid sort strategy: " + str(method))

    # Get the sort logic
    strat, order = method.split("-")

    # Sort based on filename
    if strat == "filename":
        # Check if pictures can be sorted by numeric notation
        hasNonNumber = False
        for p in pictures:
            try:
                int(PurePath(p.filename or "").stem)
            except:
                hasNonNumber = True
                break

        def sort_fct(p):
            return PurePath(p.filename or "").stem if hasNonNumber else int(PurePath(p.filename or "").stem)

        pictures.sort(key=sort_fct)

    # Sort based on picture ts
    elif strat == "time":
        # Check if all pictures have GPS ts set
        missingGpsTs = next(
            (p for p in pictures if p.metadata is None or p.metadata.ts_by_source is None or p.metadata.ts_by_source.gps is None), None
        )
        if missingGpsTs:
            # Check if all pictures have camera ts set
            missingCamTs = next(
                (p for p in pictures if p.metadata is None or p.metadata.ts_by_source is None or p.metadata.ts_by_source.camera is None),
                None,
            )
            # Sort by best ts available
            if missingCamTs:
                pictures.sort(key=lambda p: p.metadata.ts.isoformat() if p.metadata is not None else "0000-00-00T00:00:00Z")
            # Sort by camera ts
            else:
                pictures.sort(
                    key=lambda p: (
                        p.metadata.ts_by_source.camera.isoformat(),  # type: ignore
                        p.metadata.ts_by_source.gps.isoformat() if p.metadata.ts_by_source.gps else "0000-00-00T00:00:00Z",  # type: ignore
                    )
                )
        # Sort by GPS ts
        else:
            pictures.sort(
                key=lambda p: (
                    p.metadata.ts_by_source.gps.isoformat(),  # type: ignore
                    p.metadata.ts_by_source.camera.isoformat() if p.metadata.ts_by_source.camera else "0000-00-00T00:00:00Z",  # type: ignore
                )
            )

    if order == "desc":
        pictures.reverse()

    return pictures


def are_duplicates(a: Picture, b: Picture, params: MergeParams) -> Optional[Tuple[float, Optional[int]]]:
    """
    Check if 2 pictures are too similar and should be considered duplicates

    They are duplicates if they are close to each other, and for non 360 pictures, if they are roughly in the same direction.

    Note that we only consider the direction (also called heading) if it is provided by the camera (and not computed with the sequences geometries)
    since GPS can drift a bit resulting in erratic direction when waiting at a traffic light cf https://gitlab.com/panoramax/server/api/-/issues/231#note_2329723526

    Return None if not duplicates, or the distance/angle if they are
    """
    dist = a.distance_to(b)

    if params.maxDistance is None or dist > params.maxDistance:
        return None

    # Compare angle (if available on both images)
    angle = a.rotation_angle(b)
    # if one of the heading has been computed, we cannot rely on this angle being correct, so we don't consider it for the deduplication
    # it's especially important when stopped and the GPS drift a bit, cf https://gitlab.com/panoramax/server/api/-/issues/231#note_2329723526
    angle_computed = b.heading_computed or a.heading_computed
    if angle is None or angle_computed or params.maxRotationAngle is None:
        return (dist, None)
    if angle <= params.maxRotationAngle:
        return (dist, angle)
    return None


APPROX_DEGREE_TO_METER = 0.00001  # this is roughly 1m


def find_duplicates(pictures: List[Picture], params: Optional[MergeParams] = None) -> Tuple[List[Picture], List[Duplicate]]:
    """
    Finds too similar pictures.
    Note that input list should be properly sorted.

    Parameters
    ----------
    pictures : list of sorted pictures to check
    params : parameters used to consider two pictures as a duplicate

    Returns
    -------
    (Non-duplicates pictures, Duplicates pictures)
    """

    if params is None or not params.is_merge_needed() or not pictures:
        return (pictures, [])
    assert params.maxDistance is not None

    nonDups: List[Picture] = []
    duplicates = []
    duplicates_idx = set()

    rtree_index = index.Index(((i, (p.metadata.lon, p.metadata.lat, p.metadata.lon, p.metadata.lat), None) for i, p in enumerate(pictures)))

    # the rtree will give us all the neighbors in an approximated bounding box,
    # and will check, for all those pictures if some pictures are really closed, using a real haversine distance
    # we do a rough conversion between the maxDistance (in m) to degree, since it's only for the initial bounding box
    # and we use a bbox bigger than necessary (could be half by direction) to not miss duplicates due to the degree to meter approximation

    bounding_box_tolerance_approx = params.maxDistance * APPROX_DEGREE_TO_METER
    for i, currentPic in enumerate(pictures):
        if i in duplicates_idx:
            # the picture has already been flagged as duplicate by one of its neighbor, we can skip it
            continue

        bounding_box = (
            currentPic.metadata.lon - bounding_box_tolerance_approx,
            currentPic.metadata.lat - bounding_box_tolerance_approx,
            currentPic.metadata.lon + bounding_box_tolerance_approx,
            currentPic.metadata.lat + bounding_box_tolerance_approx,
        )

        near_pics_idx = rtree_index.nearest(bounding_box, num_results=100, objects=False)

        for neighbor_idx in near_pics_idx:
            if neighbor_idx == i:
                continue
            if neighbor_idx in duplicates_idx:
                continue
            neighbor = pictures[neighbor_idx]
            duplicate_details = are_duplicates(currentPic, neighbor, params)
            if duplicate_details:
                distance, angle = duplicate_details
                duplicates_idx.add(neighbor_idx)
                duplicates.append(Duplicate(picture=neighbor, duplicate_of=currentPic, distance=round(distance, 2), angle=angle))

        nonDups.append(currentPic)

    return (nonDups, duplicates)


def split_in_sequences(pictures: List[Picture], splitParams: Optional[SplitParams] = SplitParams()) -> Tuple[List[Sequence], List[Split]]:
    """
    Split a list of pictures into many sequences.
    Note that this function expect pictures to be sorted and have their metadata set.

    Parameters
    ----------
    pictures : Picture[]
            List of pictures to check, sorted and with metadata defined
    splitParams : SplitParams
            The parameters to define deltas between two pictures

    Returns
    -------
    List[Sequence]
            List of pictures splitted into smaller sequences
    """

    # No split parameters given -> just return given pictures
    if splitParams is None or not splitParams.is_split_needed():
        return ([Sequence(pictures)], [])

    sequences: List[Sequence] = []
    splits: List[Split] = []
    currentPicList: List[Picture] = []

    for pic in pictures:
        if len(currentPicList) == 0:  # No checks for 1st pic
            currentPicList.append(pic)
        else:
            lastPic = currentPicList[-1]

            # Missing metadata -> skip
            if lastPic.metadata is None or pic.metadata is None:
                currentPicList.append(pic)
                continue

            # Time delta
            timeDelta = lastPic.metadata.ts - pic.metadata.ts
            if (
                lastPic.metadata.ts_by_source
                and lastPic.metadata.ts_by_source.gps
                and pic.metadata.ts_by_source
                and pic.metadata.ts_by_source.gps
            ):
                timeDelta = lastPic.metadata.ts_by_source.gps - pic.metadata.ts_by_source.gps
            elif (
                lastPic.metadata.ts_by_source
                and lastPic.metadata.ts_by_source.camera
                and pic.metadata.ts_by_source
                and pic.metadata.ts_by_source.camera
            ):
                timeDelta = lastPic.metadata.ts_by_source.camera - pic.metadata.ts_by_source.camera
            timeOutOfDelta = False if splitParams.maxTime is None else (abs(timeDelta)).total_seconds() > splitParams.maxTime

            # Distance delta
            distance = lastPic.distance_to(pic)
            distanceOutOfDelta = False if splitParams.maxDistance is None else distance > splitParams.maxDistance

            # One of deltas maxed -> create new sequence
            if timeOutOfDelta or distanceOutOfDelta:
                sequences.append(Sequence(currentPicList))
                currentPicList = [pic]
                splits.append(Split(lastPic, pic, SplitReason.time if timeOutOfDelta else SplitReason.distance))

            # Otherwise, still in same sequence
            else:
                currentPicList.append(pic)

    sequences.append(Sequence(currentPicList))

    return (sequences, splits)


def dispatch_pictures(
    pictures: List[Picture],
    sortMethod: Optional[SortMethod] = None,
    mergeParams: Optional[MergeParams] = None,
    splitParams: Optional[SplitParams] = None,
) -> DispatchReport:
    """
    Dispatches a set of pictures into many sequences.
    This function both sorts, de-duplicates and splits in sequences all your pictures.

    Parameters
    ----------
    pictures : set of pictures to dispatch
    sortMethod : strategy for sorting pictures
    mergeParams : conditions for considering two pictures as duplicates
    splitParams : conditions for considering two sequences as distinct

    Returns
    -------
    DispatchReport : clean sequences, duplicates pictures and split reasons
    """

    # Sort
    myPics = sort_pictures(pictures, sortMethod)

    # Split in sequences
    (mySeqs, splits) = split_in_sequences(myPics, splitParams)

    # De-duplicate inside each sequences
    dups_pics = []
    for s in mySeqs:
        (myPics, dups) = find_duplicates(s.pictures, mergeParams)
        s.pictures = myPics
        dups_pics.extend(dups)

    return DispatchReport(sequences=mySeqs, duplicate_pictures=dups_pics, sequences_splits=splits)
