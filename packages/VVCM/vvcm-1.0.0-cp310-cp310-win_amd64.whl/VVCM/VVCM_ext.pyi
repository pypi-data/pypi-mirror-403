import enum
from typing import Annotated

import numpy
from numpy.typing import NDArray


class VVCM_FK_Error(enum.Enum):
    """Error Type for VVCM_FK"""

    NoError = 0
    """No Error"""

    NoSolution = 1
    """No Solution"""

    NoStableSolution = 2
    """No Stable Solution"""

    InFeasibleFormation = 3
    """Rn is not inside Vn"""

class VVCM_FK:
    """
    Get Stable Solutions of Forward Kinematics for Multi-Robot Deformable Sheet Transport System
    """

    def __init__(self, N: int, zr: float, Vn: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')]) -> None: ...

    def update_stable_solutions(self, Rn: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')]) -> VVCM_FK_Error: ...

    @property
    def N(self) -> int:
        """Number of robots"""

    @property
    def zr(self) -> float:
        """Height of holding point"""

    @property
    def Vn(self) -> Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')]:
        """Sheet shape"""

    @property
    def M(self) -> int:
        """Number of stable solutions"""

    @property
    def Rn(self) -> Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')]:
        """Current robot formation"""

    @property
    def Po(self) -> list[Annotated[NDArray[numpy.float32], dict(shape=(3), order='C')]]:
        """Object positions in world frame in all stable solutions"""

    @property
    def Vo(self) -> list[Annotated[NDArray[numpy.float32], dict(shape=(2), order='C')]]:
        """Object positions in sheet frame in all stable solutions"""

    @property
    def It(self) -> list[list[int]]:
        """Taut cable set in all stable solutions"""

    @property
    def Tn(self) -> list[int]:
        """Number of taut cables in each solution"""

    @property
    def ITn(self) -> list[int]:
        """Number of non-taut cables in each solution"""

    @property
    def stable_idxes(self) -> list[int]:
        """Indexes of stable solutions"""

    @property
    def M_all(self) -> int:
        """Number of all solutions (regardless of stability)"""

    @property
    def Po_all(self) -> list[Annotated[NDArray[numpy.float32], dict(shape=(3), order='C')]]:
        """
        Object positions in world frame in all solutions (regardless of stability)
        """

    @property
    def Vo_all(self) -> list[Annotated[NDArray[numpy.float32], dict(shape=(2), order='C')]]:
        """
        Object positions in sheet frame in all solutions (regardless of stability)
        """

    @property
    def It_all(self) -> list[list[int]]:
        """Taut cable set in all solutions (regardless of stability)"""

    @property
    def Tn_all(self) -> list[int]:
        """Number of taut cables in each solution (regardless of stability)"""

    @property
    def ITn_all(self) -> list[int]:
        """Number of non-taut cables in each solution (regardless of stability)"""

class VVCM_Simulation:
    """Simulate the VVCM system"""

    def __init__(self, N: int, zr: float, Vn: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')], Rn_initial: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')], Po_initial: Annotated[NDArray[numpy.float32], dict(shape=(3), order='C')] = ..., dt: float = 0.03333333333333333) -> None:
        """
        init the engine, all the unit of length is mm or s.

        Args:
            N: robot number
            zr: the height of holding point
            Vn: sheet shape
            Rn_initial: current robot formation
            Po_initial: current Po (unimportant, it affets the solution choosen)
            dt: time step for the simulation
        """

    def set_velocity(self, Rn_velocity: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')]) -> None:
        """
        Set velocity for the robot formation

        Args:
            Rn_velocity: N x 2 velocity vector
        """

    def step(self) -> None:
        """Simulation step"""

    def get_absolute_Rn(self) -> Annotated[NDArray[numpy.float32], dict(shape=(None, 2), order='F')]:
        """
        Get the Absolute Rn object
        Returns:
            true position of all robots
        """

    @property
    def fk_engine(self) -> VVCM_FK:
        """Forward Kinematics Engine"""

    @property
    def global_pos(self) -> Annotated[NDArray[numpy.float32], dict(shape=(2), order='C')]:
        """Global position of the formation"""

    @property
    def Rn(self) -> Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')]:
        """
        Current robot formation (the true position of all robots should be Rn + global_pos)
        """

    @property
    def Po(self) -> Annotated[NDArray[numpy.float32], dict(shape=(3), order='C')]:
        """
        Current object position (the true position of the object should be Po + global_pos)
        """

    @property
    def It(self) -> list[int]:
        """The taut cable set"""

    @property
    def solution_idx(self) -> int:
        """Index of the solution in the fk_engine"""

    @property
    def dt(self) -> float:
        """Time step for the simulation"""

    @property
    def Rn_vel(self) -> Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')]:
        """Velocity of the robots (N x 2)"""

class VVCM_ManualSimulation:
    """
    Simulation Engine for Multi-Robot Deformable Sheet Transport System.
    It does not simulate the motion of the robots, but give the stable solution
    when given the formation.
    """

    def __init__(self, N: int, zr: float, Vn: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')]) -> None: ...

    def init(self, Rn_initial: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')], Po_initial: Annotated[NDArray[numpy.float32], dict(shape=(3), order='C')] = ...) -> "std::tuple<VVCM::VVCM_FK_Error,Eigen::Matrix<float,3,1,0,3,1> >":
        """
        init the engine, all the unit of length is mm or s.

        Args:
            Rn_initial: current robot formation
            Po_initial: current Po (unimportant, it affets the solution choosen)

        Returns:
            Po
        """

    def get_new_stable_solution(self, Rn: Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')]) -> "std::tuple<VVCM::VVCM_FK_Error,Eigen::Matrix<float,3,1,0,3,1> >":
        """
        Get new stable solution with changed formation.

        Args:
            Rn: current robot formation

        Returns:
            Error info
            Po
        """

    @property
    def fk_engine(self) -> VVCM_FK:
        """Forward Kinematics Engine"""

    @property
    def global_pos(self) -> Annotated[NDArray[numpy.float32], dict(shape=(2), order='C')]:
        """Global position of the formation"""

    @property
    def Rn(self) -> Annotated[NDArray[numpy.float32], dict(shape=(None, None), order='F')]:
        """
        Current robot formation (the true position of all robots should be Rn + global_pos)
        """

    @property
    def Po(self) -> Annotated[NDArray[numpy.float32], dict(shape=(3), order='C')]:
        """
        Current object position (the true position of the object should be Po + global_pos)
        """

    @property
    def It(self) -> list[int]:
        """The taut cable set"""

    @property
    def solution_idx(self) -> int:
        """Index of the solution in the fk_engine"""
