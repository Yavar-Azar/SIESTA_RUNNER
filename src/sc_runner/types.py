from enum import Enum


class ProjectType(Enum):
    """Defines the types of projects supported."""

    SINGLE_POINT = "single_point"
    MD = "md"  # Molecular Dynamics
    GEOMETRY_OPTIMIZATION = "geometry_optimization"

