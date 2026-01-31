import logging

from gdsofa.core.component import TObject

__all__ = [
    "RequiredPlugin",
    "DefaultVisualManagerLoop",
    "DefaultAnimationLoop",
    "InteractiveCamera",
    "FreeMotionAnimationLoop",
    "VisualStyle",
    "MeshVTKLoader",
    "MeshOBJLoader",
    "MechanicalObject",
    "TetrahedronFEMForceField",
    "RestShapeSpringsForceField",
    "EulerImplicitSolver",
    "CGLinearSolver",
    "UniformMass",
    "MeshMatrixMass",
    "DiagonalMass",
    "Gravity",
    "BarycentricMapping",
    "IdentityMapping",
    "SubsetMapping",
    "PointSetTopologyContainer",
    "TriangleSetTopologyContainer",
    "TetrahedronSetTopologyContainer",
    "SurfacePressureForceField",
    "TriangleFEMForceField",
    "PointCollisionModel",
    "LineCollisionModel",
    "TriangleCollisionModel",
    "GenericConstraintSolver",
    "LinearSolverConstraintCorrection",
    "UncoupledConstraintCorrection",
    "FixedConstraint",
    "SofaHyperelasticMaterials",
    "TetrahedronHyperelasticityFEMForceField",
    "VTKExporter",
    "ConstantForceField",
    "UnstructuredGridVTKLoader",
    "PolyDataVTKLoader",
]


class RequiredPlugin(TObject):
    pass


class VisualStyle(TObject):
    def __init__(self, *flags, **kw):
        super().__init__(**kw)
        self.kw.update({"displayFlags": " ".join(flags)})


class MeshVTKLoader(TObject):
    pass


class MeshOBJLoader(TObject):
    pass


class MechanicalObject(TObject):
    pass


class RestShapeSpringsForceField(TObject):
    pass


class GenericConstraintSolver(TObject):
    def __init__(self, maxIterations=1000, tolerance=0.001, allVerified=False, **kw):
        super().__init__(**kw)
        self.kw.update(
            {
                "maxIterations": maxIterations,
                "tolerance": tolerance,
                "allVerified": allVerified,
            }
        )


class LinearSolverConstraintCorrection(TObject):
    def __init__(self, linearSolver=None, ODESolver=None, **kw):
        super().__init__(linearSolver=linearSolver, ODESolver=ODESolver, **kw)


class UncoupledConstraintCorrection(TObject):
    pass


class PointCollisionModel(TObject):
    pass


class LineCollisionModel(TObject):
    pass


class TriangleCollisionModel(TObject):
    pass


class DefaultAnimationLoop(TObject):
    pass


class DefaultVisualManagerLoop(TObject):
    pass


class InteractiveCamera(TObject):
    pass


class FreeMotionAnimationLoop(TObject):
    pass


class TetrahedronFEMForceField(TObject):
    def __init__(self, youngModulus, poissonRatio, **kw):
        super().__init__(**kw)
        self.kw.update({"youngModulus": youngModulus, "poissonRatio": poissonRatio})


class SofaHyperelasticMaterials:
    ARRUDABOYCE = "ArrudaBoyce"
    STVENANTKIRCHHOFF = "StVenantKirchhoff"
    NEOHOOKEAN = "NeoHookean"
    MOONEYRIVLIN = "MooneyRivlin"
    VERONDAWESTMAN = "VerondaWestman"
    COSTA = "Costa"
    OGDEN = "Ogden"


class TetrahedronHyperelasticityFEMForceField(TObject):
    def __init__(
        self,
        materialName=SofaHyperelasticMaterials.MOONEYRIVLIN,
        parameters=None,
        # AnisotropyDirections=None,
        topology=None,
        **kw
    ):
        super().__init__(**kw)
        self.kw.update(
            {
                "materialName": materialName,
                "ParameterSet": parameters,
                # "AnisotropyDirections": AnisotropyDirections,
                "topology": topology,
            }
        )


class TriangleFEMForceField(TObject):
    pass


class EulerImplicitSolver(TObject):
    def __init__(self, rayleighStiffness=0, rayleighMass=0, firstOrder=False, **kw):
        super().__init__(**kw)
        self.kw.update(
            {
                "rayleighStiffness": rayleighStiffness,
                "rayleighMass": rayleighMass,
                "firstOrder": firstOrder,
            }
        )


class UnstructuredGridVTKLoader(TObject):
    def __init__(self, filename: str, **kw):
        super().__init__(**kw)
        self.kw.update({"filename": filename})


class PolyDataVTKLoader(TObject):
    def __init__(self, filename: str, **kw):
        super().__init__(**kw)
        self.kw.update({"filename": filename})


class CGLinearSolver(TObject):
    def __init__(
        self,
        iterations=1000,
        tolerance=1e-12,
        threshold=1e-12,
        template="CompressedRowSparseMatrixMat3x3d",
        **kw
    ):
        super().__init__(**kw)
        self.kw.update(
            {
                "iterations": iterations,
                "tolerance": tolerance,
                "threshold": threshold,
                "template": template,
            }
        )


class UniformMass(TObject):
    def __init__(self, vertexMass=None, totalMass=None, **kw):
        super().__init__(**kw)
        for k, v in {"vertexMass": vertexMass, "totalMass": totalMass}.items():
            if v:
                self.kw[k] = v


class ConstantForceField(TObject):
    pass


class _Mass(TObject):
    def __init__(self, massDensity=None, totalMass=None, vertexMass=None, **kw):
        super().__init__(**kw)
        c = {
            "massDensity": massDensity,
            "vertexMass": vertexMass,
            "totalMass": totalMass,
        }
        for k, v in c.items():
            if v:
                self.kw[k] = v


class MeshMatrixMass(_Mass):
    pass


class DiagonalMass(_Mass):
    pass


class Gravity(TObject):
    def __init__(self, gravity=None, **kw):
        super().__init__(gravity=[0, 0, 0] if gravity is None else gravity, **kw)


class FixedConstraint(TObject):
    def __init__(self, indices, **kw):
        super().__init__(indices=indices, **kw)


class BarycentricMapping(TObject):
    pass


class SurfacePressureForceField(TObject):
    def __init__(
        self,
        topology,  # topology=Link(topo.ct)
        # tri_ncells,  # number of cells is necessary -> TODO: get it from topology
        pressure=1e6,
        name="surface_pressure",
        drawForceScale=0,
        useTangentStiffness=False,
        **kw
    ):
        super().__init__(**kw)
        self.kw.update(
            {
                "name": name,
                "pressure": pressure,
                "drawForceScale": drawForceScale,
                "useTangentStiffness": useTangentStiffness,
                "topology": topology,
                # "triangleIndices": list(range(tri_ncells)),
            }
        )


class IdentityMapping(TObject):
    pass


class SubsetMapping(TObject):
    pass


class PointSetTopologyContainer(TObject):
    pass


class TriangleSetTopologyContainer(TObject):
    def __init__(self, src=None, **kw):
        kw.update({"src": src})
        super().__init__(**kw)


class TetrahedronSetTopologyContainer(TObject):
    def __init__(self, src=None, **kw):
        kw.update({"src": src})
        super().__init__(**kw)


class VTKExporter(TObject):
    def __init__(
        self,
        filename,
        position=None,
        exportAtBegin=False,
        exportAtEnd=True,
        overwrite=False,
        exportEveryNumberOfSteps=1,
        **kw
    ):
        super().__init__(**kw)
        self.kw.update(
            {
                "filename": filename,
                "XMLformat": 0,
                "edges": 0,
                "triangles": 0,
                "tetras": 1,
                "exportAtBegin": exportAtBegin,
                "exportAtEnd": exportAtEnd,
                "position": position,
                "overwrite": overwrite,
                "exportEveryNumberOfSteps": exportEveryNumberOfSteps,
                # "listening": params.activate_exporter
            }
        )


log = logging.getLogger(__name__)
