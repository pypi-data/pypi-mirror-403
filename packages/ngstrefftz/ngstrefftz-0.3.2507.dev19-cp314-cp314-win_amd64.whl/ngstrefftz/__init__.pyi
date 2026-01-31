from __future__ import annotations
import ngsolve as ngsolve
from ngsolve.comp import BilinearForm
from ngsolve.comp import FESpace
from ngsolve.comp import L2
from ngsolve.comp import LinearForm
from ngsolve.comp import SymbolicBFI
from ngsolve.comp import SymbolicLFI
from ngsolve.fem import CoordCF
from ngsolve.fem import ET
from ngsolve.fem import IntegrationRule
import pyngcore.pyngcore
import typing
__all__: list[str] = ['AdjacentFaceSizeCF', 'BOXTYPE', 'BilinearForm', 'BoxDifferentialSymbol', 'BoxIntegral', 'ClipCoefficientFunction', 'CompoundEmbTrefftzFESpace', 'CondenseDG', 'CoordCF', 'ET', 'EmbeddedTrefftzFES', 'FESpace', 'FFacetBFI', 'FFacetLFI', 'GetWave', 'IntegrationPointFunction', 'IntegrationRule', 'L2', 'L2EmbTrefftzFESpace', 'LinearForm', 'Mesh1dTents', 'MonomialEmbTrefftzFESpace', 'PUFESpace', 'PrintCF', 'QTWaveTents1', 'QTWaveTents2', 'SpaceTimeDG_FFacetBFI', 'SpaceTimeDG_FFacetLFI', 'SymbolicBFI', 'SymbolicLFI', 'TP0FESpace', 'TWave', 'TWaveTents1', 'TWaveTents2', 'TWaveTents3', 'Tent', 'TentSlab', 'TrefftzEmbTrefftzFESpace', 'TrefftzEmbedding', 'TrefftzTents', 'VectorL2EmbTrefftzFESpace', 'WeightedRadiusFunction', 'dball', 'dbox', 'monomialfespace', 'ngsolve', 'ngstrefftz', 'trefftzfespace']
class AdjacentFaceSizeCF(ngsolve.fem.CoefficientFunction):
    def __init__(self) -> None:
        ...
class BOXTYPE:
    """
    
      Shape of subdomain for BoxIntegral, currently supported are:
      BOX: gives square or cube, in 2D or 3D
      BALL: gives circle, currently only in 2D
      
    
    Members:
    
      DEFAULT
    
      BOX
    
      BALL
    """
    BALL: typing.ClassVar[BOXTYPE]  # value = <BOXTYPE.BALL: 1>
    BOX: typing.ClassVar[BOXTYPE]  # value = <BOXTYPE.BOX: 0>
    DEFAULT: typing.ClassVar[BOXTYPE]  # value = <BOXTYPE.DEFAULT: -1>
    __members__: typing.ClassVar[dict[str, BOXTYPE]]  # value = {'DEFAULT': <BOXTYPE.DEFAULT: -1>, 'BOX': <BOXTYPE.BOX: 0>, 'BALL': <BOXTYPE.BALL: 1>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: typing.SupportsInt) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: typing.SupportsInt) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class BoxDifferentialSymbol(ngsolve.comp.DifferentialSymbol):
    """
    
    dBox that allows to formulate linear, bilinear forms and integrals on
    (bounding) boxes
    
    Example use case:
    
      dbox = BoxDifferentialSymbol()
      a = BilinearForm(...)
      a += u * v * dbox(element_boundary=...)
    
    """
    def __call__(self, definedon: ngsolve.comp.Region | str | None = None, element_boundary: bool = False, element_vb: ngsolve.comp.VorB = ..., deformation: ngsolve.comp.GridFunction = None, definedonelements: pyngcore.pyngcore.BitArray = None, bonus_intorder: typing.SupportsInt = 0, box_length: typing.SupportsFloat = 0.5, scale_with_elsize: bool = False, boxtype: BOXTYPE = ...) -> BoxDifferentialSymbol:
        """
        The call of a BoxDifferentialSymbol allows to specify what is needed to specify the
        integration domain. It returns a new BoxDifferentialSymbol.
        
        Parameters:
        
        definedon (Region or Array) : specifies on which part of the mesh (in terms of regions)
          the current form shall be defined.
        element_boundary (bool) : Does the integral take place on the boundary of an element-
          boundary?
        element_vb (VOL/BND) : Where does the integral take place from point of view
          of an element (BBND/BBBND are not implemented).
        deformation (GridFunction) : which mesh deformation shall be applied (default : None)
        definedonelements (BitArray) : Set of elements or facets where the integral shall be
          defined.
        bonus_intorder (int) : additional integration order for the integration rule (default: 0)
        box_length (double) : length of the box (default: 0.5)
        scale_with_elsize (bool) : if true, the box length is scaled with the size of the
          element (default: false)
        boxtype (BOXTYPE) : shape of the box (default: BOX)
        """
    def __init__(self) -> None:
        """
        Constructor of BoxDifferentialSymbol.
        
          Argument: none
        """
    @property
    def element_vb(self) -> ngsolve.comp.VorB:
        """
        box volume or box boundary integral on each (volume) element?
        """
    @element_vb.setter
    def element_vb(self, arg1: ngsolve.comp.VorB) -> ngsolve.comp.VorB:
        ...
class BoxIntegral(ngsolve.comp.Integral):
    """
    
            BoxIntegral allows to formulate linear, bilinear forms and integrals on
            box parts of the mesh"
    """
class CompoundEmbTrefftzFESpace(ngsolve.comp.FESpace):
    """
    
    
    
    Keyword arguments can be:
    
    order: int = 1
      order of finite element space
    complex: bool = False
      Set if FESpace should be complex
    dirichlet: regexpr
      Regular expression string defining the dirichlet boundary.
      More than one boundary can be combined by the | operator,
      i.e.: dirichlet = 'top|right'
    dirichlet_bbnd: regexpr
      Regular expression string defining the dirichlet bboundary,
      i.e. points in 2D and edges in 3D.
      More than one boundary can be combined by the | operator,
      i.e.: dirichlet_bbnd = 'top|right'
    dirichlet_bbbnd: regexpr
      Regular expression string defining the dirichlet bbboundary,
      i.e. points in 3D.
      More than one boundary can be combined by the | operator,
      i.e.: dirichlet_bbbnd = 'top|right'
    definedon: Region or regexpr
      FESpace is only defined on specific Region, created with mesh.Materials('regexpr')
      or mesh.Boundaries('regexpr'). If given a regexpr, the region is assumed to be
      mesh.Materials('regexpr').
    dim: int = 1
      Create multi dimensional FESpace (i.e. [H1]^3)
    dgjumps: bool = False
      Enable discontinuous space for DG methods, this flag is needed for DG methods,
      since the dofs have a different coupling then and this changes the sparsity
      pattern of matrices.
    autoupdate: bool = False
      Automatically update on a change to the mesh.
    low_order_space: bool = True
      Generate a lowest order space together with the high-order space,
      needed for some preconditioners.
    hoprolongation: bool = False
      Create high order prolongation operators,
      only available for H1 and L2 on simplicial meshes
    order_policy: ORDER_POLICY = ORDER_POLICY.OLDSTYLE
      CONSTANT .. use the same fixed order for all elements,
      NODAL ..... use the same order for nodes of same shape,
      VARIABLE ... use an individual order for each edge, face and cell,
      OLDSTYLE .. as it used to be for the last decade
    print: bool = False
      (historic) print some output into file set by 'SetTestoutFile'
    """
    @staticmethod
    def __flags_doc__() -> dict:
        ...
    def GetEmbedding(self) -> TrefftzEmbedding:
        """
        Get the TrefftzEmbedding
        """
    def __getstate__(self: ngsolve.comp.FESpace) -> tuple:
        ...
    def __init__(self, mesh: ngsolve.comp.Mesh, **kwargs) -> None:
        ...
    def __setstate__(self, arg0: tuple) -> None:
        ...
    @property
    def emb(self) -> TrefftzEmbedding:
        ...
class IntegrationPointFunction(ngsolve.fem.CoefficientFunction):
    def Export(self) -> list[list[float]]:
        ...
    def PrintTable(self) -> None:
        ...
    @typing.overload
    def __init__(self, mesh: ngsolve.comp.Mesh, intrule: ngsolve.fem.IntegrationRule, Vector: ngsolve.bla.VectorD) -> None:
        ...
    @typing.overload
    def __init__(self, mesh: ngsolve.comp.Mesh, intrule: ngsolve.fem.IntegrationRule, Matrix: ngsolve.bla.MatrixD) -> None:
        ...
class L2EmbTrefftzFESpace(ngsolve.comp.FESpace):
    """
    An L2-conforming finite element space.
    
    The L2 finite element space consists of element-wise polynomials,
    which are discontinuous from element to element. It uses an
    L2-orthogonal hierarchical basis which leads to orthogonal
    mass-matrices on non-curved elements.
    
    Boundary values are not meaningful for an L2 function space.
    
    The L2 space supports element-wise variable order, which can be set
    for ELEMENT-nodes.
    
    Per default, all dofs are local dofs and are condensed if static
    condensation is performed. The lowest order can be kept in the
    WIRE_BASKET via the flag 'lowest_order_wb=True'.
    
    All dofs can be hidden. Then the basis functions don't show up in the
    global system.
    
    Keyword arguments can be:
    
    order: int = 1
      order of finite element space
    complex: bool = False
      Set if FESpace should be complex
    dirichlet: regexpr
      Regular expression string defining the dirichlet boundary.
      More than one boundary can be combined by the | operator,
      i.e.: dirichlet = 'top|right'
    dirichlet_bbnd: regexpr
      Regular expression string defining the dirichlet bboundary,
      i.e. points in 2D and edges in 3D.
      More than one boundary can be combined by the | operator,
      i.e.: dirichlet_bbnd = 'top|right'
    dirichlet_bbbnd: regexpr
      Regular expression string defining the dirichlet bbboundary,
      i.e. points in 3D.
      More than one boundary can be combined by the | operator,
      i.e.: dirichlet_bbbnd = 'top|right'
    definedon: Region or regexpr
      FESpace is only defined on specific Region, created with mesh.Materials('regexpr')
      or mesh.Boundaries('regexpr'). If given a regexpr, the region is assumed to be
      mesh.Materials('regexpr').
    dim: int = 1
      Create multi dimensional FESpace (i.e. [H1]^3)
    dgjumps: bool = False
      Enable discontinuous space for DG methods, this flag is needed for DG methods,
      since the dofs have a different coupling then and this changes the sparsity
      pattern of matrices.
    autoupdate: bool = False
      Automatically update on a change to the mesh.
    low_order_space: bool = True
      Generate a lowest order space together with the high-order space,
      needed for some preconditioners.
    hoprolongation: bool = False
      Create high order prolongation operators,
      only available for H1 and L2 on simplicial meshes
    order_policy: ORDER_POLICY = ORDER_POLICY.OLDSTYLE
      CONSTANT .. use the same fixed order for all elements,
      NODAL ..... use the same order for nodes of same shape,
      VARIABLE ... use an individual order for each edge, face and cell,
      OLDSTYLE .. as it used to be for the last decade
    print: bool = False
      (historic) print some output into file set by 'SetTestoutFile'
    all_dofs_together: bool = True
      Change ordering of dofs. If this flag ist set,
      all dofs of an element are ordered successively.
      Otherwise, the lowest order dofs (the constants)
      of all elements are ordered first.
    lowest_order_wb: bool = False
      Keep lowest order dof in WIRE_BASKET
    hide_all_dofs: bool = False
      Set all used dofs to HIDDEN_DOFs
    tp: bool = False
      Use sum-factorization for evaluation
    """
    @staticmethod
    def __flags_doc__() -> dict:
        ...
    def GetEmbedding(self) -> TrefftzEmbedding:
        """
        Get the TrefftzEmbedding
        """
    def __getstate__(self: ngsolve.comp.FESpace) -> tuple:
        ...
    def __init__(self, mesh: ngsolve.comp.Mesh, **kwargs) -> None:
        ...
    def __setstate__(self, arg0: tuple) -> None:
        ...
    @property
    def emb(self) -> TrefftzEmbedding:
        ...
class MonomialEmbTrefftzFESpace(ngsolve.comp.FESpace):
    """
    
    
    
    Keyword arguments can be:
    
    order: int = 1
      order of finite element space
    complex: bool = False
      Set if FESpace should be complex
    dirichlet: regexpr
      Regular expression string defining the dirichlet boundary.
      More than one boundary can be combined by the | operator,
      i.e.: dirichlet = 'top|right'
    dirichlet_bbnd: regexpr
      Regular expression string defining the dirichlet bboundary,
      i.e. points in 2D and edges in 3D.
      More than one boundary can be combined by the | operator,
      i.e.: dirichlet_bbnd = 'top|right'
    dirichlet_bbbnd: regexpr
      Regular expression string defining the dirichlet bbboundary,
      i.e. points in 3D.
      More than one boundary can be combined by the | operator,
      i.e.: dirichlet_bbbnd = 'top|right'
    definedon: Region or regexpr
      FESpace is only defined on specific Region, created with mesh.Materials('regexpr')
      or mesh.Boundaries('regexpr'). If given a regexpr, the region is assumed to be
      mesh.Materials('regexpr').
    dim: int = 1
      Create multi dimensional FESpace (i.e. [H1]^3)
    dgjumps: bool = False
      Enable discontinuous space for DG methods, this flag is needed for DG methods,
      since the dofs have a different coupling then and this changes the sparsity
      pattern of matrices.
    autoupdate: bool = False
      Automatically update on a change to the mesh.
    low_order_space: bool = True
      Generate a lowest order space together with the high-order space,
      needed for some preconditioners.
    hoprolongation: bool = False
      Create high order prolongation operators,
      only available for H1 and L2 on simplicial meshes
    order_policy: ORDER_POLICY = ORDER_POLICY.OLDSTYLE
      CONSTANT .. use the same fixed order for all elements,
      NODAL ..... use the same order for nodes of same shape,
      VARIABLE ... use an individual order for each edge, face and cell,
      OLDSTYLE .. as it used to be for the last decade
    print: bool = False
      (historic) print some output into file set by 'SetTestoutFile'
    useshift: bool = True
      shift of basis functins to element center
    usescale: bool = True
      scale element basis functions with diam
    """
    @staticmethod
    def __flags_doc__() -> dict:
        ...
    def GetEmbedding(self) -> TrefftzEmbedding:
        """
        Get the TrefftzEmbedding
        """
    def __getstate__(self: ngsolve.comp.FESpace) -> tuple:
        ...
    def __init__(self, mesh: ngsolve.comp.Mesh, **kwargs) -> None:
        ...
    def __setstate__(self, arg0: tuple) -> None:
        ...
    @property
    def emb(self) -> TrefftzEmbedding:
        ...
class PUFESpace(ngsolve.comp.FESpace):
    """
    
    
    
    Keyword arguments can be:
    
    order: int = 1
      order of finite element space
    complex: bool = False
      Set if FESpace should be complex
    dirichlet: regexpr
      Regular expression string defining the dirichlet boundary.
      More than one boundary can be combined by the | operator,
      i.e.: dirichlet = 'top|right'
    dirichlet_bbnd: regexpr
      Regular expression string defining the dirichlet bboundary,
      i.e. points in 2D and edges in 3D.
      More than one boundary can be combined by the | operator,
      i.e.: dirichlet_bbnd = 'top|right'
    dirichlet_bbbnd: regexpr
      Regular expression string defining the dirichlet bbboundary,
      i.e. points in 3D.
      More than one boundary can be combined by the | operator,
      i.e.: dirichlet_bbbnd = 'top|right'
    definedon: Region or regexpr
      FESpace is only defined on specific Region, created with mesh.Materials('regexpr')
      or mesh.Boundaries('regexpr'). If given a regexpr, the region is assumed to be
      mesh.Materials('regexpr').
    dim: int = 1
      Create multi dimensional FESpace (i.e. [H1]^3)
    dgjumps: bool = False
      Enable discontinuous space for DG methods, this flag is needed for DG methods,
      since the dofs have a different coupling then and this changes the sparsity
      pattern of matrices.
    autoupdate: bool = False
      Automatically update on a change to the mesh.
    low_order_space: bool = True
      Generate a lowest order space together with the high-order space,
      needed for some preconditioners.
    hoprolongation: bool = False
      Create high order prolongation operators,
      only available for H1 and L2 on simplicial meshes
    order_policy: ORDER_POLICY = ORDER_POLICY.OLDSTYLE
      CONSTANT .. use the same fixed order for all elements,
      NODAL ..... use the same order for nodes of same shape,
      VARIABLE ... use an individual order for each edge, face and cell,
      OLDSTYLE .. as it used to be for the last decade
    print: bool = False
      (historic) print some output into file set by 'SetTestoutFile'
    useshift: bool = True
      shift of basis functins to element center
    usescale: bool = True
      scale element basis functions with diam
    """
    @staticmethod
    def GetDocu() -> ...:
        ...
    @staticmethod
    def __flags_doc__() -> dict:
        ...
    def __getstate__(self: ngsolve.comp.FESpace) -> tuple:
        ...
    def __init__(self, mesh: ngsolve.comp.Mesh, **kwargs) -> None:
        ...
    def __setstate__(self, arg0: tuple) -> None:
        ...
class PrintCF(ngsolve.fem.CoefficientFunction):
    """
    
    CoefficientFunction that writes integration point (in world coords.)
    into a file whenever evaluated at one.
    """
    def __init__(self, filename: str) -> None:
        """
        Constructor of PrintCF (integration point (in world coords.) printing coefficientfunction).
          Argument: filename (string) : name of the file where the values shall be printed
        """
class QTWaveTents1(TrefftzTents):
    def Energy(self, arg0: ngsolve.bla.MatrixD) -> float:
        ...
    def Error(self, arg0: ngsolve.bla.MatrixD, arg1: ngsolve.bla.MatrixD) -> float:
        ...
    def GetInitmesh(self) -> ngsolve.comp.Mesh:
        ...
    def GetOrder(self) -> int:
        ...
    def GetSpaceDim(self) -> int:
        ...
    def GetWave(self, U):
        ...
    def GetWavefront(self) -> ngsolve.bla.MatrixD:
        ...
    def L2Error(self, arg0: ngsolve.bla.MatrixD, arg1: ngsolve.bla.MatrixD) -> float:
        ...
    def LocalDofs(self) -> int:
        ...
    def MakeWavefront(self, arg0: ngsolve.fem.CoefficientFunction, arg1: typing.SupportsFloat) -> ngsolve.bla.MatrixD:
        ...
    def MaxAdiam(self) -> float:
        ...
class QTWaveTents2(TrefftzTents):
    def Energy(self, arg0: ngsolve.bla.MatrixD) -> float:
        ...
    def Error(self, arg0: ngsolve.bla.MatrixD, arg1: ngsolve.bla.MatrixD) -> float:
        ...
    def GetInitmesh(self) -> ngsolve.comp.Mesh:
        ...
    def GetOrder(self) -> int:
        ...
    def GetSpaceDim(self) -> int:
        ...
    def GetWave(self, U):
        ...
    def GetWavefront(self) -> ngsolve.bla.MatrixD:
        ...
    def L2Error(self, arg0: ngsolve.bla.MatrixD, arg1: ngsolve.bla.MatrixD) -> float:
        ...
    def LocalDofs(self) -> int:
        ...
    def MakeWavefront(self, arg0: ngsolve.fem.CoefficientFunction, arg1: typing.SupportsFloat) -> ngsolve.bla.MatrixD:
        ...
    def MaxAdiam(self) -> float:
        ...
class TP0FESpace(ngsolve.comp.FESpace):
    """
    L2 FES with zero boundary on quads
    
    The space is meant as a test space for embedded Trefftz methods.
          On quadrilateral elements, the shape functions are zero on the longer
          edges of the element. On triangular elements, standard L2 shape functions
          of order (order-2) are used.
          
    Keyword arguments can be:
    
    order: int = 1
      order of finite element space
    complex: bool = False
      Set if FESpace should be complex
    dirichlet: regexpr
      Regular expression string defining the dirichlet boundary.
      More than one boundary can be combined by the | operator,
      i.e.: dirichlet = 'top|right'
    dirichlet_bbnd: regexpr
      Regular expression string defining the dirichlet bboundary,
      i.e. points in 2D and edges in 3D.
      More than one boundary can be combined by the | operator,
      i.e.: dirichlet_bbnd = 'top|right'
    dirichlet_bbbnd: regexpr
      Regular expression string defining the dirichlet bbboundary,
      i.e. points in 3D.
      More than one boundary can be combined by the | operator,
      i.e.: dirichlet_bbbnd = 'top|right'
    definedon: Region or regexpr
      FESpace is only defined on specific Region, created with mesh.Materials('regexpr')
      or mesh.Boundaries('regexpr'). If given a regexpr, the region is assumed to be
      mesh.Materials('regexpr').
    dim: int = 1
      Create multi dimensional FESpace (i.e. [H1]^3)
    dgjumps: bool = False
      Enable discontinuous space for DG methods, this flag is needed for DG methods,
      since the dofs have a different coupling then and this changes the sparsity
      pattern of matrices.
    autoupdate: bool = False
      Automatically update on a change to the mesh.
    low_order_space: bool = True
      Generate a lowest order space together with the high-order space,
      needed for some preconditioners.
    hoprolongation: bool = False
      Create high order prolongation operators,
      only available for H1 and L2 on simplicial meshes
    order_policy: ORDER_POLICY = ORDER_POLICY.OLDSTYLE
      CONSTANT .. use the same fixed order for all elements,
      NODAL ..... use the same order for nodes of same shape,
      VARIABLE ... use an individual order for each edge, face and cell,
      OLDSTYLE .. as it used to be for the last decade
    print: bool = False
      (historic) print some output into file set by 'SetTestoutFile'
    allow_both_axes_zero: bool = False
      If true, on quadrilateral elements with equal edge lengths,
      both coordinate axes are treated as zero axes.
    small_quad: double = 0
      If nonzero, both axes zero only applies to quads smaller than 
      this threshold.
    """
    @staticmethod
    def __flags_doc__() -> dict:
        ...
    def __getstate__(self: ngsolve.comp.FESpace) -> tuple:
        ...
    def __init__(self, mesh: ngsolve.comp.Mesh, **kwargs) -> None:
        ...
    def __setstate__(self, arg0: tuple) -> None:
        ...
class TWaveTents1(TrefftzTents):
    def Energy(self, arg0: ngsolve.bla.MatrixD) -> float:
        ...
    def Error(self, arg0: ngsolve.bla.MatrixD, arg1: ngsolve.bla.MatrixD) -> float:
        ...
    def GetInitmesh(self) -> ngsolve.comp.Mesh:
        ...
    def GetOrder(self) -> int:
        ...
    def GetSpaceDim(self) -> int:
        ...
    def GetWave(self, U):
        ...
    def GetWavefront(self) -> ngsolve.bla.MatrixD:
        ...
    def L2Error(self, arg0: ngsolve.bla.MatrixD, arg1: ngsolve.bla.MatrixD) -> float:
        ...
    def LocalDofs(self) -> int:
        ...
    def MakeWavefront(self, arg0: ngsolve.fem.CoefficientFunction, arg1: typing.SupportsFloat) -> ngsolve.bla.MatrixD:
        ...
    def MaxAdiam(self) -> float:
        ...
class TWaveTents2(TrefftzTents):
    def Energy(self, arg0: ngsolve.bla.MatrixD) -> float:
        ...
    def Error(self, arg0: ngsolve.bla.MatrixD, arg1: ngsolve.bla.MatrixD) -> float:
        ...
    def GetInitmesh(self) -> ngsolve.comp.Mesh:
        ...
    def GetOrder(self) -> int:
        ...
    def GetSpaceDim(self) -> int:
        ...
    def GetWave(self, U):
        ...
    def GetWavefront(self) -> ngsolve.bla.MatrixD:
        ...
    def L2Error(self, arg0: ngsolve.bla.MatrixD, arg1: ngsolve.bla.MatrixD) -> float:
        ...
    def LocalDofs(self) -> int:
        ...
    def MakeWavefront(self, arg0: ngsolve.fem.CoefficientFunction, arg1: typing.SupportsFloat) -> ngsolve.bla.MatrixD:
        ...
    def MaxAdiam(self) -> float:
        ...
class TWaveTents3(TrefftzTents):
    def Energy(self, arg0: ngsolve.bla.MatrixD) -> float:
        ...
    def Error(self, arg0: ngsolve.bla.MatrixD, arg1: ngsolve.bla.MatrixD) -> float:
        ...
    def GetInitmesh(self) -> ngsolve.comp.Mesh:
        ...
    def GetOrder(self) -> int:
        ...
    def GetSpaceDim(self) -> int:
        ...
    def GetWave(self, U):
        ...
    def GetWavefront(self) -> ngsolve.bla.MatrixD:
        ...
    def L2Error(self, arg0: ngsolve.bla.MatrixD, arg1: ngsolve.bla.MatrixD) -> float:
        ...
    def LocalDofs(self) -> int:
        ...
    def MakeWavefront(self, arg0: ngsolve.fem.CoefficientFunction, arg1: typing.SupportsFloat) -> ngsolve.bla.MatrixD:
        ...
    def MaxAdiam(self) -> float:
        ...
class Tent:
    """
    Tent structure
    """
    def MaxSlope(self) -> float:
        ...
    @property
    def els(self) -> pyngcore.pyngcore.Array_I_S:
        ...
    @property
    def internal_facets(self) -> pyngcore.pyngcore.Array_I_S:
        ...
    @property
    def level(self) -> int:
        ...
    @property
    def nbtime(self) -> pyngcore.pyngcore.Array_D_S:
        ...
    @property
    def nbv(self) -> pyngcore.pyngcore.Array_I_S:
        ...
    @property
    def tbot(self) -> float:
        ...
    @property
    def ttop(self) -> float:
        ...
    @property
    def vertex(self) -> int:
        ...
class TentSlab:
    """
    Tent pitched slab in D + 1 time dimensions
    """
    def DrawPitchedTentsVTK(self, vtkfilename: str = 'vtkoutput') -> None:
        """
                 Export the mesh of tents and intermediate advancing fronts
                 to VTK file format for visualization in Paraview.
        """
    def GetNLayers(self) -> int:
        ...
    def GetNTents(self) -> int:
        ...
    def GetSlabHeight(self) -> float:
        ...
    def GetTent(self, arg0: typing.SupportsInt) -> Tent:
        ...
    def MaxSlope(self) -> float:
        ...
    def PitchTents(self, dt: typing.SupportsFloat, local_ct: bool = False, global_ct: typing.SupportsFloat = 1.0) -> bool:
        """
                 Parameters:--
                   dt: spacetime slab's height in time.
                   local_ct: if True, constrain tent slope by scaling 1/wavespeed
                     with a further local mesh-dependent factor.
                   global_ct: an additional factor to constrain tent slope, which
                     gives flatter tents for smaller values.
        
                 Returns True upon successful tent meshing.
                 -------------
        """
    def SetMaxWavespeed(self, arg0: typing.Any) -> None:
        ...
    def TentData1D(self) -> list:
        ...
    def __init__(self, mesh: ngsolve.comp.Mesh, method: str = 'edge', heapsize: typing.SupportsInt = 1000000) -> None:
        ...
    @property
    def gradphi(self) -> ngsolve.fem.CoefficientFunction:
        ...
    @property
    def mesh(self) -> ngsolve.comp.Mesh:
        ...
class TrefftzEmbTrefftzFESpace(ngsolve.comp.FESpace):
    """
    Trefftz space for different PDEs. Use kwarg 'eq' to choose the PDE, currently implemented are:
     - laplace - for Laplace equation
     - qtelliptic - for the quasi-Trefftz space for an elliptic problem
     - wave - for the second order acoustic wave equation
     - qtwave - for the quasi-Trefftz space
     - fowave - for the first order acoustic wave equation, returns TnT (sigv,tauw)
     - foqtwave - for the quasi-Trefftz space 
     - helmholtz - planewaves for the helmholtz equation
     - helmholtzconj - returns the complex conjungate of the planewaves 
    
    
    
    Keyword arguments can be:
    
    eq: string
      Choose type of Trefftz functions.
    order: int = 1
      Order of finite element space
    dgjumps: bool = True
      Enable discontinuous space for DG methods, this flag is always True for trefftzfespace.
    complex: bool = False
      Set if FESpace should be complex
    useshift: bool = True
      shift of basis functins to element center
    usescale: bool = True
      scale element basis functions with diam
    """
    @staticmethod
    def __flags_doc__() -> dict:
        ...
    def GetEmbedding(self) -> TrefftzEmbedding:
        """
        Get the TrefftzEmbedding
        """
    def __getstate__(self: ngsolve.comp.FESpace) -> tuple:
        ...
    def __init__(self, mesh: ngsolve.comp.Mesh, **kwargs) -> None:
        ...
    def __setstate__(self, arg0: tuple) -> None:
        ...
    @property
    def emb(self) -> TrefftzEmbedding:
        ...
class TrefftzEmbedding:
    """
    
                    Gives access to the embedding matrix and a particular solution and
                    can be used to construct an EmbeddedTrefftzFESpace.
    
                    The dimension of the local Trefftz space is determined by the kernel of `top`,
                    after removing the dofs fixed by the conforming condition in `cop` and `crhs`.
    
                    If a different test space is used, the dimension of the local Trefftz space is
                    at best dim(fes)-dim(fes_test) and may increase by zero singular values of `top`
                    (with respect to the threshold `eps`).
                
    """
    @typing.overload
    def Embed(self, arg0: ngsolve.la.BaseVector) -> ngsolve.la.BaseVector:
        """
        Embed a Trefftz GridFunction Vector into the underlying FESpace
        """
    @typing.overload
    def Embed(self, arg0: ngsolve.comp.GridFunction) -> ngsolve.comp.GridFunction:
        """
        Embed a Trefftz GridFunction into the underlying FESpace
        """
    def GetEmbedding(self) -> ngsolve.la.BaseMatrix:
        """
        Get the sparse embedding matrix
        """
    @typing.overload
    def GetParticularSolution(self) -> ngsolve.la.BaseVector:
        """
        Particular solution as GridFunction vector of the underlying FESpace
        """
    @typing.overload
    def GetParticularSolution(self, arg0: ngsolve.comp.SumOfIntegrals) -> ngsolve.la.BaseVector:
        """
        Particular solution as GridFunction vector of the underlying FESpace, given a trhs
        """
    @typing.overload
    def GetParticularSolution(self, arg0: ngsolve.la.BaseVector) -> ngsolve.la.BaseVector:
        """
        Particular solution as GridFunction vector of the underlying FESpace, given a trhs as vector
        """
    def __init__(self, top: ngsolve.comp.SumOfIntegrals = None, trhs: ngsolve.comp.SumOfIntegrals = None, cop: ngsolve.comp.SumOfIntegrals = None, crhs: ngsolve.comp.SumOfIntegrals = None, ndof_trefftz: typing.SupportsInt = 18446744073709551615, eps: typing.SupportsFloat = 0.0, fes: ngsolve.comp.FESpace = None, fes_test: ngsolve.comp.FESpace = None, fes_conformity: ngsolve.comp.FESpace = None, fes_ip: ngsolve.comp.SumOfIntegrals = None, ignoredofs: pyngcore.pyngcore.BitArray = None, stats: dict | None = None) -> None:
        """
                        Constructs a new Trefftz embedding object.
        
                         :param top: the differential operation. Can be None
                         :param trhs: right hand side of the var. formulation
                         :param cop: left hand side of the conformity operation
                         :param crhs: right hand side of the conformity operation
                         :param eps: cutoff for singular values from the SVD of the local operator.
                                values below eps are considered zero and therefore in the kernel of `top`.
                                (default: 0.0)
                         :param ndof_trefftz: fixes the number of degrees of freedom per element
                             that are to be considered in the Trefftz space generated by `top`
                             (i.e. the local dimension of the kernel of `top` on one element)
                             cannot be used together with `eps` (default: 0)
                         :param fes: the finite element space of `top` (optional, determined
                             from `top` if not given)
                         :param fes_test: the finite element test space of `top` (optional,
                             determined from `top` if not given)
                         :param fes_conformity: finite element space of the conformity operation (optional,
                             determined from `cop` if not given)
                         :param ignoredofs: BitArray of dofs from fes to be ignored in the embedding
                         :param stats: optional dictionary to store statistics about the singular values,
                             input dictionary is modified
        """
    @property
    def fes(self) -> ngsolve.comp.FESpace:
        ...
    @property
    def fes_conformity(self) -> ngsolve.comp.FESpace:
        ...
    @property
    def fes_test(self) -> ngsolve.comp.FESpace:
        ...
class TrefftzTents:
    def Propagate(self) -> None:
        """
        Solve tent slab
        """
    def SetBoundaryCF(self, arg0: ngsolve.fem.CoefficientFunction) -> None:
        """
        Set boundary condition
        """
    def SetInitial(self, arg0: ngsolve.fem.CoefficientFunction) -> None:
        """
        Set initial condition
        """
class VectorL2EmbTrefftzFESpace(ngsolve.comp.FESpace):
    """
    A vector-valued L2-conforming finite element space.
    
    The Vector-L2 finite element space is a product-space of L2 spaces,
    where the number of components coincides with the mesh dimension.
    
    It is implemented by means of a CompoundFESpace, as one could do it at the
    user-level. Additionally, some operators are added for convenience and performance:
    One can evaluate the vector-valued function, and one can take the gradient.
    
    Keyword arguments can be:
    
    order: int = 1
      order of finite element space
    complex: bool = False
      Set if FESpace should be complex
    dirichlet: regexpr
      Regular expression string defining the dirichlet boundary.
      More than one boundary can be combined by the | operator,
      i.e.: dirichlet = 'top|right'
    dirichlet_bbnd: regexpr
      Regular expression string defining the dirichlet bboundary,
      i.e. points in 2D and edges in 3D.
      More than one boundary can be combined by the | operator,
      i.e.: dirichlet_bbnd = 'top|right'
    dirichlet_bbbnd: regexpr
      Regular expression string defining the dirichlet bbboundary,
      i.e. points in 3D.
      More than one boundary can be combined by the | operator,
      i.e.: dirichlet_bbbnd = 'top|right'
    definedon: Region or regexpr
      FESpace is only defined on specific Region, created with mesh.Materials('regexpr')
      or mesh.Boundaries('regexpr'). If given a regexpr, the region is assumed to be
      mesh.Materials('regexpr').
    dim: int = 1
      Create multi dimensional FESpace (i.e. [H1]^3)
    dgjumps: bool = False
      Enable discontinuous space for DG methods, this flag is needed for DG methods,
      since the dofs have a different coupling then and this changes the sparsity
      pattern of matrices.
    autoupdate: bool = False
      Automatically update on a change to the mesh.
    low_order_space: bool = True
      Generate a lowest order space together with the high-order space,
      needed for some preconditioners.
    hoprolongation: bool = False
      Create high order prolongation operators,
      only available for H1 and L2 on simplicial meshes
    order_policy: ORDER_POLICY = ORDER_POLICY.OLDSTYLE
      CONSTANT .. use the same fixed order for all elements,
      NODAL ..... use the same order for nodes of same shape,
      VARIABLE ... use an individual order for each edge, face and cell,
      OLDSTYLE .. as it used to be for the last decade
    print: bool = False
      (historic) print some output into file set by 'SetTestoutFile'
    piola: bool = False
      Use Piola transform to map to physical element
      allows to use the div-differential operator.
    covariant: bool = False
      Use the covariant transform to map to physical element
      allows to use the curl-differential operator.
    all_dofs_together: bool = True
      dofs within one scalar component are together.
    hide_all_dofs: bool = False
      all dofs are condensed without a global dofnr
    lowest_order_wb: bool = False
      Keep lowest order dof in WIRE_BASKET
    tp: bool = False
      Use sum-factorization for evaluation
    """
    @staticmethod
    def __flags_doc__() -> dict:
        ...
    def GetEmbedding(self) -> TrefftzEmbedding:
        """
        Get the TrefftzEmbedding
        """
    def __getstate__(self: ngsolve.comp.FESpace) -> tuple:
        ...
    def __init__(self, mesh: ngsolve.comp.Mesh, **kwargs) -> None:
        ...
    def __setstate__(self, arg0: tuple) -> None:
        ...
    @property
    def emb(self) -> TrefftzEmbedding:
        ...
class WeightedRadiusFunction(ngsolve.fem.CoefficientFunction):
    def __init__(self, mesh: ngsolve.comp.Mesh, CoefficientFunction: ngsolve.fem.CoefficientFunction) -> None:
        ...
class monomialfespace(ngsolve.comp.FESpace):
    """
    
    
    
    Keyword arguments can be:
    
    order: int = 1
      order of finite element space
    complex: bool = False
      Set if FESpace should be complex
    dirichlet: regexpr
      Regular expression string defining the dirichlet boundary.
      More than one boundary can be combined by the | operator,
      i.e.: dirichlet = 'top|right'
    dirichlet_bbnd: regexpr
      Regular expression string defining the dirichlet bboundary,
      i.e. points in 2D and edges in 3D.
      More than one boundary can be combined by the | operator,
      i.e.: dirichlet_bbnd = 'top|right'
    dirichlet_bbbnd: regexpr
      Regular expression string defining the dirichlet bbboundary,
      i.e. points in 3D.
      More than one boundary can be combined by the | operator,
      i.e.: dirichlet_bbbnd = 'top|right'
    definedon: Region or regexpr
      FESpace is only defined on specific Region, created with mesh.Materials('regexpr')
      or mesh.Boundaries('regexpr'). If given a regexpr, the region is assumed to be
      mesh.Materials('regexpr').
    dim: int = 1
      Create multi dimensional FESpace (i.e. [H1]^3)
    dgjumps: bool = False
      Enable discontinuous space for DG methods, this flag is needed for DG methods,
      since the dofs have a different coupling then and this changes the sparsity
      pattern of matrices.
    autoupdate: bool = False
      Automatically update on a change to the mesh.
    low_order_space: bool = True
      Generate a lowest order space together with the high-order space,
      needed for some preconditioners.
    hoprolongation: bool = False
      Create high order prolongation operators,
      only available for H1 and L2 on simplicial meshes
    order_policy: ORDER_POLICY = ORDER_POLICY.OLDSTYLE
      CONSTANT .. use the same fixed order for all elements,
      NODAL ..... use the same order for nodes of same shape,
      VARIABLE ... use an individual order for each edge, face and cell,
      OLDSTYLE .. as it used to be for the last decade
    print: bool = False
      (historic) print some output into file set by 'SetTestoutFile'
    useshift: bool = True
      shift of basis functins to element center
    usescale: bool = True
      scale element basis functions with diam
    """
    @staticmethod
    def GetDocu() -> ...:
        ...
    @staticmethod
    def __flags_doc__() -> dict:
        ...
    def SetCoeff(self, arg0: ngsolve.fem.CoefficientFunction) -> None:
        ...
    def __getstate__(self: ngsolve.comp.FESpace) -> tuple:
        ...
    def __init__(self, mesh: ngsolve.comp.Mesh, **kwargs) -> None:
        ...
    def __setstate__(self, arg0: tuple) -> None:
        ...
class trefftzfespace(ngsolve.comp.FESpace):
    """
    Trefftz space for different PDEs. Use kwarg 'eq' to choose the PDE, currently implemented are:
     - laplace - for Laplace equation
     - qtelliptic - for the quasi-Trefftz space for an elliptic problem
     - wave - for the second order acoustic wave equation
     - qtwave - for the quasi-Trefftz space
     - fowave - for the first order acoustic wave equation, returns TnT (sigv,tauw)
     - foqtwave - for the quasi-Trefftz space 
     - helmholtz - planewaves for the helmholtz equation
     - helmholtzconj - returns the complex conjungate of the planewaves 
    
    
    
    Keyword arguments can be:
    
    eq: string
      Choose type of Trefftz functions.
    order: int = 1
      Order of finite element space
    dgjumps: bool = True
      Enable discontinuous space for DG methods, this flag is always True for trefftzfespace.
    complex: bool = False
      Set if FESpace should be complex
    useshift: bool = True
      shift of basis functins to element center
    usescale: bool = True
      scale element basis functions with diam
    """
    @staticmethod
    def GetDocu() -> ...:
        ...
    @staticmethod
    def __flags_doc__() -> dict:
        ...
    def GetParticularSolution(self, acoeffF: ngsolve.fem.CoefficientFunction) -> ngsolve.comp.GridFunction:
        """
                        Compute a element-wise particular solution for given right hand side.
        
                        Parameters
                        ----------
                        coeffF : CoefficientFunction
                            Right hand side
        """
    @typing.overload
    def SetCoeff(self, coeff_const: typing.SupportsFloat) -> None:
        ...
    @typing.overload
    def SetCoeff(self, acoeffA: ngsolve.fem.CoefficientFunction, acoeffB: ngsolve.fem.CoefficientFunction = None, acoeffC: ngsolve.fem.CoefficientFunction = None) -> None:
        """
                        Set coefficient of Trefftz space.
        
                        For an elliptic problem, the coefficients are given by
                        - div(coeffA*grad(u)) + coeffB*grad(u) + coeffC u = 0
        
                        For the first order wave equation, the coefficients are given by
                        grad(v) + coeffB dt sigma = 0
                        div(sigma) + 1/coeffA**2 dt v = 0
        
                        For the second order wave equation, the coefficients are given by
                        - div(1/coeffB grad(u)) + 1/coeffA**2 dtt u = 0
        
                        Parameters
                        ----------
                        coeffA : CoefficientFunction
                            Coefficient A
                        coeffB : CoefficientFunction
                            Coefficient B
                        coeffC : CoefficientFunction
                            Coefficient C
        """
    def __getstate__(self: ngsolve.comp.FESpace) -> tuple:
        ...
    def __init__(self, mesh: ngsolve.comp.Mesh, **kwargs) -> None:
        ...
    def __setstate__(self, arg0: tuple) -> None:
        ...
def ClipCoefficientFunction(arg0: ngsolve.fem.CoefficientFunction, arg1: typing.SupportsInt, arg2: typing.SupportsFloat) -> ngsolve.fem.CoefficientFunction:
    ...
def CondenseDG(mat: BaseMatrix, vec: ngsolve.la.BaseVector, ncondense: ngsolve.comp.FESpace) -> BaseMatrix:
    """
          hello
    """
def EmbeddedTrefftzFES(emb: TrefftzEmbedding) -> ngsolve.comp.FESpace:
    """
            Given a TrefftzEmbedding this wrapper produces a Trefftz FESpace using local projections,
            following the Embedded Trefftz-DG methodology.
    
            :param TrefftzEmbedding: The Trefftz embedding object.
    
            :return: EmbTrefftzFES
    """
def FFacetBFI(form: ngsolve.fem.CoefficientFunction, VOL_or_BND: ngsolve.comp.VorB = ..., element_boundary: bool = False, skeleton: bool = True, definedon: ngsolve.comp.Region | list | None = None, intrule: ngsolve.fem.IntegrationRule = ..., bonus_intorder: typing.SupportsInt = 0, definedonelements: pyngcore.pyngcore.BitArray = None, simd_evaluate: bool = False, element_vb: ngsolve.comp.VorB = ..., geom_free: bool = False, deformation: ngsolve.comp.GridFunction = None) -> ngsolve.fem.BFI:
    """
    A symbolic bilinear form integrator, operating on facet intersections.
    
    Parameters:
    
    VOL_or_BND : ngsolve.comp.VorB
      input VOL, BND
    
    skeleton : bool
      must be True
    """
def FFacetLFI(form: ngsolve.fem.CoefficientFunction, VOL_or_BND: ngsolve.comp.VorB = ..., element_boundary: bool = False, skeleton: bool = True, definedon: ngsolve.comp.Region | list | None = None, intrule: ngsolve.fem.IntegrationRule = ..., bonus_intorder: typing.SupportsInt = 0, definedonelements: pyngcore.pyngcore.BitArray = None, simd_evaluate: bool = False, element_vb: ngsolve.comp.VorB = ..., deformation: ngsolve.comp.GridFunction = None) -> ngsolve.fem.LFI:
    """
    A symbolic linear form integrator, operating on facet intersections.
    
    Parameters:
    
    VOL_or_BND : ngsolve.comp.VorB
      input VOL, BND
    
    skeleton : bool
      must be True
    """
def GetWave(self, U):
    ...
def Mesh1dTents(arg0: TentSlab) -> ngsolve.comp.Mesh:
    ...
def SpaceTimeDG_FFacetBFI(mesh: ngsolve.comp.Mesh, coef_c: ngsolve.fem.CoefficientFunction, coef_sig: ngsolve.fem.CoefficientFunction, VOL_or_BND: ngsolve.comp.VorB) -> ngsolve.fem.BFI:
    ...
def SpaceTimeDG_FFacetLFI(mesh: ngsolve.comp.Mesh, gfuh: ngsolve.fem.CoefficientFunction, gfduh: ngsolve.fem.CoefficientFunction, coef_c: ngsolve.fem.CoefficientFunction, coef_sig: ngsolve.fem.CoefficientFunction, VOL_or_BND: ngsolve.comp.VorB) -> ngsolve.fem.LFI:
    ...
def TWave(order: typing.SupportsInt, tps: TentSlab, wavespeedcf: ngsolve.fem.CoefficientFunction, BBcf: ngsolve.fem.CoefficientFunction = None) -> TrefftzTents:
    """
                    Create solver for acoustiv wave equation on tent-pitched mesh.
    
                    :param order: Polynomial order of the Trefftz space.
                    :param tps: Tent-pitched slab.
                    :param wavespeedcf: PDE Coefficient
                    :param BB: PDE Coefficient
    """
dball: BoxDifferentialSymbol  # value = <ngstrefftz.BoxDifferentialSymbol object>
dbox: BoxDifferentialSymbol  # value = <ngstrefftz.BoxDifferentialSymbol object>
ngstrefftz = 
