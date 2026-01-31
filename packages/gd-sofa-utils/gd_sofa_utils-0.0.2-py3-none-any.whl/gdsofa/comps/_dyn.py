from gdsofa.core.component import TObject

__all__ = [
	"REQUIRED_PLUGINS",
	"MappedObject",
	"ConstraintAnimationLoop",
	"MultiStepAnimationLoop",
	"MultiTagAnimationLoop",
	"APIVersion",
	"AddResourceRepository",
	"InfoComponent",
	"MakeAliasComponent",
	"MakeDataAliasComponent",
	"MessageHandlerComponent",
	"PauseAnimation",
	"PauseAnimationOnEvent",
	"BaseProximityIntersection",
	"DiscreteIntersection",
	"LocalMinDistance",
	"MeshDiscreteIntersection",
	"MeshMinProximityIntersection",
	"MeshNewProximityIntersection",
	"MinProximityIntersection",
	"NewProximityIntersection",
	"RayDiscreteIntersection",
	"RayNewProximityIntersection",
	"TetrahedronDiscreteIntersection",
	"BVHNarrowPhase",
	"BruteForceBroadPhase",
	"BruteForceDetection",
	"CollisionPipeline",
	"DSAPBox",
	"DirectSAP",
	"DirectSAPNarrowPhase",
	"IncrSAP",
	"RayTraceDetection",
	"RayTraceNarrowPhase",
	"CubeModel",
	"CylinderModel",
	"LineModel",
	"PointModel",
	"RayModel",
	"SphereModel",
	"TetrahedronModel",
	"TriangleModel",
	"TriangleModelInRegularGrid",
	"TriangleOctreeModel",
	"BarycentricContactMapper",
	"BaseContactMapper",
	"IdentityContactMapper",
	"RigidContactMapper",
	"SubsetContactMapper",
	"TetrahedronBarycentricContactMapper",
	"AugmentedLagrangianResponse",
	"BarycentricPenalityContact",
	"BarycentricStickContact",
	"CollisionResponse",
	"ContactIdentifier",
	"ContactListener",
	"FrictionContact",
	"PenalityContactForceField",
	"RayContact",
	"RuleBasedContactManager",
	"StickContactConstraint",
	"TetrahedronAugmentedLagrangianContact",
	"TetrahedronBarycentricPenalityContact",
	"TetrahedronFrictionContact",
	"TetrahedronRayContact",
	"AffineMovementProjectiveConstraint",
	"AttachProjectiveConstraint",
	"DirectionProjectiveConstraint",
	"FixedPlaneProjectiveConstraint",
	"FixedProjectiveConstraint",
	"FixedRotationProjectiveConstraint",
	"FixedTranslationProjectiveConstraint",
	"HermiteSplineProjectiveConstraint",
	"LineProjectiveConstraint",
	"LinearMovementProjectiveConstraint",
	"LinearVelocityProjectiveConstraint",
	"OscillatorProjectiveConstraint",
	"ParabolicProjectiveConstraint",
	"PartialFixedProjectiveConstraint",
	"PartialLinearMovementProjectiveConstraint",
	"PatchTestMovementProjectiveConstraint",
	"PlaneProjectiveConstraint",
	"PointProjectiveConstraint",
	"PositionBasedDynamicsProjectiveConstraint",
	"SkeletalMotionProjectiveConstraint",
	"AugmentedLagrangianConstraint",
	"BilateralLagrangianConstraint",
	"FixedLagrangianConstraint",
	"SlidingLagrangianConstraint",
	"StopperLagrangianConstraint",
	"UniformLagrangianConstraint",
	"UnilateralLagrangianConstraint",
	"ConstraintSolverImpl",
	"ConstraintStoreLambdaVisitor",
	"GenericConstraintProblem",
	"LCPConstraintSolver",
	"MechanicalGetConstraintResolutionVisitor",
	"MechanicalGetConstraintViolationVisitor",
	"GenericConstraintCorrection",
	"PrecomputedConstraintCorrection",
	"DifferenceEngine",
	"DilateEngine",
	"DisplacementMatrixEngine",
	"IndexValueMapper",
	"Indices2ValuesMapper",
	"MapIndices",
	"MathOp",
	"ProjectiveTransformEngine",
	"QuatToRigidEngine",
	"ROIValueMapper",
	"RigidToQuatEngine",
	"SmoothMeshEngine",
	"TransformEngine",
	"TransformMatrixEngine",
	"TransformPosition",
	"Vertex2Frame",
	"BoxROI",
	"ComplementaryROI",
	"IndicesFromValues",
	"MergeROIs",
	"MeshBoundaryROI",
	"MeshROI",
	"MeshSampler",
	"MeshSplittingEngine",
	"MeshSubsetEngine",
	"NearestPointROI",
	"PairBoxRoi",
	"PlaneROI",
	"PointsFromIndices",
	"ProximityROI",
	"SelectConnectedLabelsROI",
	"SelectLabelROI",
	"SphereROI",
	"SubsetTopology",
	"ValuesFromIndices",
	"ValuesFromPositions",
	"AverageCoord",
	"ClusteringEngine",
	"Distances",
	"HausdorffDistance",
	"ShapeMatching",
	"SumEngine",
	"ExtrudeEdgesAndGenerateQuads",
	"ExtrudeQuadsAndGenerateHexas",
	"ExtrudeSurface",
	"GenerateCylinder",
	"GenerateGrid",
	"GenerateRigidMass",
	"GenerateSphere",
	"GroupFilterYoungModulus",
	"JoinPoints",
	"MergeMeshes",
	"MergePoints",
	"MergeSets",
	"MergeVectors",
	"MeshBarycentricMapperEngine",
	"MeshClosingEngine",
	"MeshTetraStuffing",
	"NormEngine",
	"NormalsFromPoints",
	"RandomPointDistributionInSurface",
	"Spiral",
	"BackgroundSetting",
	"MouseButtonSetting",
	"SofaDefaultPathSetting",
	"StatsSetting",
	"ViewerSetting",
	"AMDOrderingMethod",
	"COLAMDOrderingMethod",
	"NaturalOrderingMethod",
	"GraphScatteredTypes",
	"LinearSystemData",
	"MatrixFreeSystem",
	"MatrixLinearSolver",
	"MatrixLinearSystem",
	"MinResLinearSolver",
	"PCGLinearSolver",
	"AsyncSparseLDLSolver",
	"BTDLinearSolver",
	"CholeskySolver",
	"EigenSimplicialLDLT",
	"EigenSimplicialLLT",
	"EigenSolverFactory",
	"EigenSparseLU",
	"EigenSparseQR",
	"MatrixLinearSystem",
	"PrecomputedLinearSolver",
	"SVDLinearSolver",
	"SparseCommon",
	"SparseLDLSolver",
	"TypedMatrixLinearSystem",
	"BlockJacobiPreconditioner",
	"JacobiPreconditioner",
	"PrecomputedMatrixSystem",
	"PrecomputedWarpPreconditioner",
	"RotationMatrixSystem",
	"SSORPreconditioner",
	"WarpPreconditioner",
	"ConicalForceField",
	"DiagonalVelocityDampingForceField",
	"EdgePressureForceField",
	"EllipsoidForceField",
	"InteractionEllipsoidForceField",
	"LinearForceField",
	"OscillatingTorsionPressureForceField",
	"PlaneForceField",
	"QuadPressureForceField",
	"SphereForceField",
	"TaitSurfacePressureForceField",
	"TorsionForceField",
	"TrianglePressureForceField",
	"UniformVelocityDampingForceField",
	"BaseCamera",
	"Camera",
	"CylinderVisualModel",
	"LineAxis",
	"RecordedCamera",
	"TrailRenderer",
	"Visual3DText",
	"VisualGrid",
	"VisualModelImpl",
	"VisualTransform",
	"CentralDifferenceSolver",
	"DampVelocitySolver",
	"EulerExplicitSolver",
	"RungeKutta2Solver",
	"RungeKutta4Solver",
	"NewmarkImplicitSolver",
	"StaticSolver",
	"VariationalSymplecticSolver",
	"CompareState",
	"CompareTopology",
	"InputEventReader",
	"ReadState",
	"ReadTopology",
	"WriteState",
	"WriteTopology",
	"Controller",
	"MechanicalStateController",
	"TetrahedronDiffusionFEMForceField",
	"AngularSpringForceField",
	"FastTriangularBendingSprings",
	"FrameSpringForceField",
	"GearSpringForceField",
	"JointSpring",
	"JointSpringForceField",
	"LinearSpring",
	"MeshSpringForceField",
	"PolynomialRestShapeSpringsForceField",
	"PolynomialSpringsForceField",
	"QuadBendingSprings",
	"QuadularBendingSprings",
	"RegularGridSpringForceField",
	"RepulsiveSpringForceField",
	"SpringForceField",
	"TriangleBendingSprings",
	"TriangularBendingSprings",
	"TriangularBiquadraticSpringsForceField",
	"TriangularQuadraticSpringsForceField",
	"VectorSpringForceField",
	"TetrahedralTensorMassForceField",
	"TriangularTensorMassForceField",
	"PlasticMaterial",
	"StandardTetrahedralFEMForceField",
	"BaseLinearElasticityFEMForceField",
	"BeamFEMForceField",
	"FastTetrahedralCorotationalForceField",
	"HexahedralFEMForceField",
	"HexahedralFEMForceFieldAndMass",
	"HexahedronFEMForceField",
	"HexahedronFEMForceFieldAndMass",
	"QuadBendingFEMForceField",
	"TetrahedralCorotationalFEMForceField",
	"TriangleFEMUtils",
	"TriangularAnisotropicFEMForceField",
	"TriangularFEMForceField",
	"TriangularFEMForceFieldOptim",
	"HexahedronCompositeFEMForceFieldAndMass",
	"HexahedronCompositeFEMMapping",
	"NonUniformHexahedralFEMForceFieldAndMass",
	"NonUniformHexahedronFEMForceFieldAndMass",
	"AffinePatch_test",
	"LinearElasticity_test",
	"BaseVTKReader",
	"BlenderExporter",
	"GIDMeshLoader",
	"GridMeshCreator",
	"MeshExporter",
	"MeshGmshLoader",
	"MeshOffLoader",
	"MeshSTLLoader",
	"MeshTrianLoader",
	"MeshXspLoader",
	"OffSequenceLoader",
	"STLExporter",
	"SphereLoader",
	"StringMeshCreator",
	"VisualModelOBJExporter",
	"VoxelGridLoader",
	"AssembleGlobalVectorFromLocalVectorVisitor",
	"BaseMatrixProjectionMethod",
	"CompositeLinearSystem",
	"ConstantSparsityPatternSystem",
	"ConstantSparsityProjectionMethod",
	"DispatchFromGlobalVectorToLocalVectorVisitor",
	"MappedMassMatrixObserver",
	"MappingGraph",
	"MatrixLinearSystem",
	"MatrixProjectionMethod",
	"TypedMatrixLinearSystem",
	"TopologicalChangeProcessor",
	"TopologyBoundingTrasher",
	"TopologyChecker",
	"CylinderGridTopology",
	"GridTopology",
	"RegularGridTopology",
	"SparseGridMultipleTopology",
	"SparseGridRamificationTopology",
	"SparseGridTopology",
	"SphereGridTopology",
	"CubeTopology",
	"MeshTopology",
	"SphereQuadTopology",
	"DynamicSparseGridGeometryAlgorithms",
	"DynamicSparseGridTopologyContainer",
	"DynamicSparseGridTopologyModifier",
	"EdgeSetGeometryAlgorithms",
	"EdgeSetTopologyContainer",
	"EdgeSetTopologyModifier",
	"HexahedronSetGeometryAlgorithms",
	"HexahedronSetTopologyContainer",
	"HexahedronSetTopologyModifier",
	"MultilevelHexahedronSetTopologyContainer",
	"NumericalIntegrationDescriptor",
	"PointSetGeometryAlgorithms",
	"PointSetTopologyModifier",
	"QuadSetGeometryAlgorithms",
	"QuadSetTopologyContainer",
	"QuadSetTopologyModifier",
	"TetrahedronSetGeometryAlgorithms",
	"TetrahedronSetTopologyModifier",
	"TriangleSetGeometryAlgorithms",
	"TriangleSetTopologyModifier",
	"CenterPointTopologicalMapping",
	"Edge2QuadTopologicalMapping",
	"Hexa2QuadTopologicalMapping",
	"Hexa2TetraTopologicalMapping",
	"IdentityTopologicalMapping",
	"Quad2TriangleTopologicalMapping",
	"SubsetTopologicalMapping",
	"Tetra2TriangleTopologicalMapping",
	"Triangle2EdgeTopologicalMapping",
	"AreaMapping",
	"DistanceFromTargetMapping",
	"DistanceMapping",
	"DistanceMultiMapping",
	"RigidMapping",
	"SquareDistanceMapping",
	"SquareMapping",
	"VolumeMapping",
	"BarycentricMapper",
	"BarycentricMapperEdgeSetTopology",
	"BarycentricMapperHexahedronSetTopology",
	"BarycentricMapperMeshTopology",
	"BarycentricMapperQuadSetTopology",
	"BarycentricMapperRegularGridTopology",
	"BarycentricMapperSparseGridTopology",
	"BarycentricMapperTetrahedronSetTopology",
	"BarycentricMapperTopologyContainer",
	"BarycentricMapperTriangleSetTopology",
	"BarycentricMappingRigid",
	"BeamLinearMapping",
	"CenterOfMassMapping",
	"CenterOfMassMulti2Mapping",
	"CenterOfMassMultiMapping",
	"DeformableOnRigidFrameMapping",
	"IdentityMultiMapping",
	"LineSetSkinningMapping",
	"Mesh2PointMechanicalMapping",
	"Mesh2PointTopologicalMapping",
	"SimpleTesselatedHexaTopologicalMapping",
	"SimpleTesselatedTetraMechanicalMapping",
	"SimpleTesselatedTetraTopologicalMapping",
	"SkinningMapping",
	"SubsetMultiMapping",
	"TopologyBarycentricMapper",
	"TubularMapping",
	"VoidMapping",
	"ForceFeedback",
	"LCPForceFeedback",
	"NullForceFeedback",
	"NullForceFeedbackT",
	"TextureInterpolation",
	"CompositingVisualLoop",
	"Light",
	"LightManager",
	"OglAttribute",
	"OglOITShader",
	"OglRenderingSRGB",
	"OglShader",
	"OglShaderMacro",
	"OglShaderVisualModel",
	"OglShadowShader",
	"OglTexture",
	"OglTexturePointer",
	"OglVariable",
	"OrderIndependentTransparencyManager",
	"PostProcessManager",
	"VisualManagerPass",
	"VisualManagerSecondaryPass",
	"OglColorMap",
	"OglLabel",
	"OglViewport",
	"ClipPlane",
	"DataDisplay",
	"MergeVisualModels",
	"OglModel",
	"OglSceneFrame",
	"PointSplatModel",
	"SlicedVolumetricModel",
	"Axis",
	"BasicShapesGL",
	"Capture",
	"Cylinder",
	"DrawToolGL",
	"FrameBufferObject",
	"GLSLShader",
	"Texture",
	"TransformationGL",
	"VideoRecorderFFMPEG",
]


class MappedObject(TObject):
	pass

class ConstraintAnimationLoop(TObject):
	pass

class MultiStepAnimationLoop(TObject):
	pass

class MultiTagAnimationLoop(TObject):
	pass

class APIVersion(TObject):
	pass

class AddResourceRepository(TObject):
	pass

class InfoComponent(TObject):
	pass

class MakeAliasComponent(TObject):
	pass

class MakeDataAliasComponent(TObject):
	pass

class MessageHandlerComponent(TObject):
	pass

class PauseAnimation(TObject):
	pass

class PauseAnimationOnEvent(TObject):
	pass

class BaseProximityIntersection(TObject):
	pass

class DiscreteIntersection(TObject):
	pass

class LocalMinDistance(TObject):
	pass

class MeshDiscreteIntersection(TObject):
	pass

class MeshMinProximityIntersection(TObject):
	pass

class MeshNewProximityIntersection(TObject):
	pass

class MinProximityIntersection(TObject):
	pass

class NewProximityIntersection(TObject):
	pass

class RayDiscreteIntersection(TObject):
	pass

class RayNewProximityIntersection(TObject):
	pass

class TetrahedronDiscreteIntersection(TObject):
	pass

class BVHNarrowPhase(TObject):
	pass

class BruteForceBroadPhase(TObject):
	pass

class BruteForceDetection(TObject):
	pass

class CollisionPipeline(TObject):
	pass

class DSAPBox(TObject):
	pass

class DirectSAP(TObject):
	pass

class DirectSAPNarrowPhase(TObject):
	pass

class IncrSAP(TObject):
	pass

class RayTraceDetection(TObject):
	pass

class RayTraceNarrowPhase(TObject):
	pass

class CubeModel(TObject):
	pass

class CylinderModel(TObject):
	pass

class LineModel(TObject):
	pass

class PointModel(TObject):
	pass

class RayModel(TObject):
	pass

class SphereModel(TObject):
	pass

class TetrahedronModel(TObject):
	pass

class TriangleModel(TObject):
	pass

class TriangleModelInRegularGrid(TObject):
	pass

class TriangleOctreeModel(TObject):
	pass

class BarycentricContactMapper(TObject):
	pass

class BaseContactMapper(TObject):
	pass

class IdentityContactMapper(TObject):
	pass

class RigidContactMapper(TObject):
	pass

class SubsetContactMapper(TObject):
	pass

class TetrahedronBarycentricContactMapper(TObject):
	pass

class AugmentedLagrangianResponse(TObject):
	pass

class BarycentricPenalityContact(TObject):
	pass

class BarycentricStickContact(TObject):
	pass

class CollisionResponse(TObject):
	pass

class ContactIdentifier(TObject):
	pass

class ContactListener(TObject):
	pass

class FrictionContact(TObject):
	pass

class PenalityContactForceField(TObject):
	pass

class RayContact(TObject):
	pass

class RuleBasedContactManager(TObject):
	pass

class StickContactConstraint(TObject):
	pass

class TetrahedronAugmentedLagrangianContact(TObject):
	pass

class TetrahedronBarycentricPenalityContact(TObject):
	pass

class TetrahedronFrictionContact(TObject):
	pass

class TetrahedronRayContact(TObject):
	pass

class AffineMovementProjectiveConstraint(TObject):
	pass

class AttachProjectiveConstraint(TObject):
	pass

class DirectionProjectiveConstraint(TObject):
	pass

class FixedPlaneProjectiveConstraint(TObject):
	pass

class FixedProjectiveConstraint(TObject):
	pass

class FixedRotationProjectiveConstraint(TObject):
	pass

class FixedTranslationProjectiveConstraint(TObject):
	pass

class HermiteSplineProjectiveConstraint(TObject):
	pass

class LineProjectiveConstraint(TObject):
	pass

class LinearMovementProjectiveConstraint(TObject):
	pass

class LinearVelocityProjectiveConstraint(TObject):
	pass

class OscillatorProjectiveConstraint(TObject):
	pass

class ParabolicProjectiveConstraint(TObject):
	pass

class PartialFixedProjectiveConstraint(TObject):
	pass

class PartialLinearMovementProjectiveConstraint(TObject):
	pass

class PatchTestMovementProjectiveConstraint(TObject):
	pass

class PlaneProjectiveConstraint(TObject):
	pass

class PointProjectiveConstraint(TObject):
	pass

class PositionBasedDynamicsProjectiveConstraint(TObject):
	pass

class SkeletalMotionProjectiveConstraint(TObject):
	pass

class AugmentedLagrangianConstraint(TObject):
	pass

class BilateralLagrangianConstraint(TObject):
	pass

class FixedLagrangianConstraint(TObject):
	pass

class SlidingLagrangianConstraint(TObject):
	pass

class StopperLagrangianConstraint(TObject):
	pass

class UniformLagrangianConstraint(TObject):
	pass

class UnilateralLagrangianConstraint(TObject):
	pass

class ConstraintSolverImpl(TObject):
	pass

class ConstraintStoreLambdaVisitor(TObject):
	pass

class GenericConstraintProblem(TObject):
	pass

class LCPConstraintSolver(TObject):
	pass

class MechanicalGetConstraintResolutionVisitor(TObject):
	pass

class MechanicalGetConstraintViolationVisitor(TObject):
	pass

class GenericConstraintCorrection(TObject):
	pass

class PrecomputedConstraintCorrection(TObject):
	pass

class DifferenceEngine(TObject):
	pass

class DilateEngine(TObject):
	pass

class DisplacementMatrixEngine(TObject):
	pass

class IndexValueMapper(TObject):
	pass

class Indices2ValuesMapper(TObject):
	pass

class MapIndices(TObject):
	pass

class MathOp(TObject):
	pass

class ProjectiveTransformEngine(TObject):
	pass

class QuatToRigidEngine(TObject):
	pass

class ROIValueMapper(TObject):
	pass

class RigidToQuatEngine(TObject):
	pass

class SmoothMeshEngine(TObject):
	pass

class TransformEngine(TObject):
	pass

class TransformMatrixEngine(TObject):
	pass

class TransformPosition(TObject):
	pass

class Vertex2Frame(TObject):
	pass

class BoxROI(TObject):
	pass

class ComplementaryROI(TObject):
	pass

class IndicesFromValues(TObject):
	pass

class MergeROIs(TObject):
	pass

class MeshBoundaryROI(TObject):
	pass

class MeshROI(TObject):
	pass

class MeshSampler(TObject):
	pass

class MeshSplittingEngine(TObject):
	pass

class MeshSubsetEngine(TObject):
	pass

class NearestPointROI(TObject):
	pass

class PairBoxRoi(TObject):
	pass

class PlaneROI(TObject):
	pass

class PointsFromIndices(TObject):
	pass

class ProximityROI(TObject):
	pass

class SelectConnectedLabelsROI(TObject):
	pass

class SelectLabelROI(TObject):
	pass

class SphereROI(TObject):
	pass

class SubsetTopology(TObject):
	pass

class ValuesFromIndices(TObject):
	pass

class ValuesFromPositions(TObject):
	pass

class AverageCoord(TObject):
	pass

class ClusteringEngine(TObject):
	pass

class Distances(TObject):
	pass

class HausdorffDistance(TObject):
	pass

class ShapeMatching(TObject):
	pass

class SumEngine(TObject):
	pass

class ExtrudeEdgesAndGenerateQuads(TObject):
	pass

class ExtrudeQuadsAndGenerateHexas(TObject):
	pass

class ExtrudeSurface(TObject):
	pass

class GenerateCylinder(TObject):
	pass

class GenerateGrid(TObject):
	pass

class GenerateRigidMass(TObject):
	pass

class GenerateSphere(TObject):
	pass

class GroupFilterYoungModulus(TObject):
	pass

class JoinPoints(TObject):
	pass

class MergeMeshes(TObject):
	pass

class MergePoints(TObject):
	pass

class MergeSets(TObject):
	pass

class MergeVectors(TObject):
	pass

class MeshBarycentricMapperEngine(TObject):
	pass

class MeshClosingEngine(TObject):
	pass

class MeshTetraStuffing(TObject):
	pass

class NormEngine(TObject):
	pass

class NormalsFromPoints(TObject):
	pass

class RandomPointDistributionInSurface(TObject):
	pass

class Spiral(TObject):
	pass

class BackgroundSetting(TObject):
	pass

class MouseButtonSetting(TObject):
	pass

class SofaDefaultPathSetting(TObject):
	pass

class StatsSetting(TObject):
	pass

class ViewerSetting(TObject):
	pass

class AMDOrderingMethod(TObject):
	pass

class COLAMDOrderingMethod(TObject):
	pass

class NaturalOrderingMethod(TObject):
	pass

class GraphScatteredTypes(TObject):
	pass

class LinearSystemData(TObject):
	pass

class MatrixFreeSystem(TObject):
	pass

class MatrixLinearSolver(TObject):
	pass

class MatrixLinearSystem(TObject):
	pass

class MinResLinearSolver(TObject):
	pass

class PCGLinearSolver(TObject):
	pass

class AsyncSparseLDLSolver(TObject):
	pass

class BTDLinearSolver(TObject):
	pass

class CholeskySolver(TObject):
	pass

class EigenSimplicialLDLT(TObject):
	pass

class EigenSimplicialLLT(TObject):
	pass

class EigenSolverFactory(TObject):
	pass

class EigenSparseLU(TObject):
	pass

class EigenSparseQR(TObject):
	pass

class MatrixLinearSystem(TObject):
	pass

class PrecomputedLinearSolver(TObject):
	pass

class SVDLinearSolver(TObject):
	pass

class SparseCommon(TObject):
	pass

class SparseLDLSolver(TObject):
	pass

class TypedMatrixLinearSystem(TObject):
	pass

class BlockJacobiPreconditioner(TObject):
	pass

class JacobiPreconditioner(TObject):
	pass

class PrecomputedMatrixSystem(TObject):
	pass

class PrecomputedWarpPreconditioner(TObject):
	pass

class RotationMatrixSystem(TObject):
	pass

class SSORPreconditioner(TObject):
	pass

class WarpPreconditioner(TObject):
	pass

class ConicalForceField(TObject):
	pass

class DiagonalVelocityDampingForceField(TObject):
	pass

class EdgePressureForceField(TObject):
	pass

class EllipsoidForceField(TObject):
	pass

class InteractionEllipsoidForceField(TObject):
	pass

class LinearForceField(TObject):
	pass

class OscillatingTorsionPressureForceField(TObject):
	pass

class PlaneForceField(TObject):
	pass

class QuadPressureForceField(TObject):
	pass

class SphereForceField(TObject):
	pass

class TaitSurfacePressureForceField(TObject):
	pass

class TorsionForceField(TObject):
	pass

class TrianglePressureForceField(TObject):
	pass

class UniformVelocityDampingForceField(TObject):
	pass

class BaseCamera(TObject):
	pass

class Camera(TObject):
	pass

class CylinderVisualModel(TObject):
	pass

class LineAxis(TObject):
	pass

class RecordedCamera(TObject):
	pass

class TrailRenderer(TObject):
	pass

class Visual3DText(TObject):
	pass

class VisualGrid(TObject):
	pass

class VisualModelImpl(TObject):
	pass

class VisualTransform(TObject):
	pass

class CentralDifferenceSolver(TObject):
	pass

class DampVelocitySolver(TObject):
	pass

class EulerExplicitSolver(TObject):
	pass

class RungeKutta2Solver(TObject):
	pass

class RungeKutta4Solver(TObject):
	pass

class NewmarkImplicitSolver(TObject):
	pass

class StaticSolver(TObject):
	pass

class VariationalSymplecticSolver(TObject):
	pass

class CompareState(TObject):
	pass

class CompareTopology(TObject):
	pass

class InputEventReader(TObject):
	pass

class ReadState(TObject):
	pass

class ReadTopology(TObject):
	pass

class WriteState(TObject):
	pass

class WriteTopology(TObject):
	pass

class Controller(TObject):
	pass

class MechanicalStateController(TObject):
	pass

class TetrahedronDiffusionFEMForceField(TObject):
	pass

class AngularSpringForceField(TObject):
	pass

class FastTriangularBendingSprings(TObject):
	pass

class FrameSpringForceField(TObject):
	pass

class GearSpringForceField(TObject):
	pass

class JointSpring(TObject):
	pass

class JointSpringForceField(TObject):
	pass

class LinearSpring(TObject):
	pass

class MeshSpringForceField(TObject):
	pass

class PolynomialRestShapeSpringsForceField(TObject):
	pass

class PolynomialSpringsForceField(TObject):
	pass

class QuadBendingSprings(TObject):
	pass

class QuadularBendingSprings(TObject):
	pass

class RegularGridSpringForceField(TObject):
	pass

class RepulsiveSpringForceField(TObject):
	pass

class SpringForceField(TObject):
	pass

class TriangleBendingSprings(TObject):
	pass

class TriangularBendingSprings(TObject):
	pass

class TriangularBiquadraticSpringsForceField(TObject):
	pass

class TriangularQuadraticSpringsForceField(TObject):
	pass

class VectorSpringForceField(TObject):
	pass

class TetrahedralTensorMassForceField(TObject):
	pass

class TriangularTensorMassForceField(TObject):
	pass

class PlasticMaterial(TObject):
	pass

class StandardTetrahedralFEMForceField(TObject):
	pass

class BaseLinearElasticityFEMForceField(TObject):
	pass

class BeamFEMForceField(TObject):
	pass

class FastTetrahedralCorotationalForceField(TObject):
	pass

class HexahedralFEMForceField(TObject):
	pass

class HexahedralFEMForceFieldAndMass(TObject):
	pass

class HexahedronFEMForceField(TObject):
	pass

class HexahedronFEMForceFieldAndMass(TObject):
	pass

class QuadBendingFEMForceField(TObject):
	pass

class TetrahedralCorotationalFEMForceField(TObject):
	pass

class TriangleFEMUtils(TObject):
	pass

class TriangularAnisotropicFEMForceField(TObject):
	pass

class TriangularFEMForceField(TObject):
	pass

class TriangularFEMForceFieldOptim(TObject):
	pass

class HexahedronCompositeFEMForceFieldAndMass(TObject):
	pass

class HexahedronCompositeFEMMapping(TObject):
	pass

class NonUniformHexahedralFEMForceFieldAndMass(TObject):
	pass

class NonUniformHexahedronFEMForceFieldAndMass(TObject):
	pass

class AffinePatch_test(TObject):
	pass

class LinearElasticity_test(TObject):
	pass

class BaseVTKReader(TObject):
	pass

class BlenderExporter(TObject):
	pass

class GIDMeshLoader(TObject):
	pass

class GridMeshCreator(TObject):
	pass

class MeshExporter(TObject):
	pass

class MeshGmshLoader(TObject):
	pass

class MeshOffLoader(TObject):
	pass

class MeshSTLLoader(TObject):
	pass

class MeshTrianLoader(TObject):
	pass

class MeshXspLoader(TObject):
	pass

class OffSequenceLoader(TObject):
	pass

class STLExporter(TObject):
	pass

class SphereLoader(TObject):
	pass

class StringMeshCreator(TObject):
	pass

class VisualModelOBJExporter(TObject):
	pass

class VoxelGridLoader(TObject):
	pass

class AssembleGlobalVectorFromLocalVectorVisitor(TObject):
	pass

class BaseMatrixProjectionMethod(TObject):
	pass

class CompositeLinearSystem(TObject):
	pass

class ConstantSparsityPatternSystem(TObject):
	pass

class ConstantSparsityProjectionMethod(TObject):
	pass

class DispatchFromGlobalVectorToLocalVectorVisitor(TObject):
	pass

class MappedMassMatrixObserver(TObject):
	pass

class MappingGraph(TObject):
	pass

class MatrixLinearSystem(TObject):
	pass

class MatrixProjectionMethod(TObject):
	pass

class TypedMatrixLinearSystem(TObject):
	pass

class TopologicalChangeProcessor(TObject):
	pass

class TopologyBoundingTrasher(TObject):
	pass

class TopologyChecker(TObject):
	pass

class CylinderGridTopology(TObject):
	pass

class GridTopology(TObject):
	pass

class RegularGridTopology(TObject):
	pass

class SparseGridMultipleTopology(TObject):
	pass

class SparseGridRamificationTopology(TObject):
	pass

class SparseGridTopology(TObject):
	pass

class SphereGridTopology(TObject):
	pass

class CubeTopology(TObject):
	pass

class MeshTopology(TObject):
	pass

class SphereQuadTopology(TObject):
	pass

class DynamicSparseGridGeometryAlgorithms(TObject):
	pass

class DynamicSparseGridTopologyContainer(TObject):
	pass

class DynamicSparseGridTopologyModifier(TObject):
	pass

class EdgeSetGeometryAlgorithms(TObject):
	pass

class EdgeSetTopologyContainer(TObject):
	pass

class EdgeSetTopologyModifier(TObject):
	pass

class HexahedronSetGeometryAlgorithms(TObject):
	pass

class HexahedronSetTopologyContainer(TObject):
	pass

class HexahedronSetTopologyModifier(TObject):
	pass

class MultilevelHexahedronSetTopologyContainer(TObject):
	pass

class NumericalIntegrationDescriptor(TObject):
	pass

class PointSetGeometryAlgorithms(TObject):
	pass

class PointSetTopologyModifier(TObject):
	pass

class QuadSetGeometryAlgorithms(TObject):
	pass

class QuadSetTopologyContainer(TObject):
	pass

class QuadSetTopologyModifier(TObject):
	pass

class TetrahedronSetGeometryAlgorithms(TObject):
	pass

class TetrahedronSetTopologyModifier(TObject):
	pass

class TriangleSetGeometryAlgorithms(TObject):
	pass

class TriangleSetTopologyModifier(TObject):
	pass

class CenterPointTopologicalMapping(TObject):
	pass

class Edge2QuadTopologicalMapping(TObject):
	pass

class Hexa2QuadTopologicalMapping(TObject):
	pass

class Hexa2TetraTopologicalMapping(TObject):
	pass

class IdentityTopologicalMapping(TObject):
	pass

class Quad2TriangleTopologicalMapping(TObject):
	pass

class SubsetTopologicalMapping(TObject):
	pass

class Tetra2TriangleTopologicalMapping(TObject):
	pass

class Triangle2EdgeTopologicalMapping(TObject):
	pass

class AreaMapping(TObject):
	pass

class DistanceFromTargetMapping(TObject):
	pass

class DistanceMapping(TObject):
	pass

class DistanceMultiMapping(TObject):
	pass

class RigidMapping(TObject):
	pass

class SquareDistanceMapping(TObject):
	pass

class SquareMapping(TObject):
	pass

class VolumeMapping(TObject):
	pass

class BarycentricMapper(TObject):
	pass

class BarycentricMapperEdgeSetTopology(TObject):
	pass

class BarycentricMapperHexahedronSetTopology(TObject):
	pass

class BarycentricMapperMeshTopology(TObject):
	pass

class BarycentricMapperQuadSetTopology(TObject):
	pass

class BarycentricMapperRegularGridTopology(TObject):
	pass

class BarycentricMapperSparseGridTopology(TObject):
	pass

class BarycentricMapperTetrahedronSetTopology(TObject):
	pass

class BarycentricMapperTopologyContainer(TObject):
	pass

class BarycentricMapperTriangleSetTopology(TObject):
	pass

class BarycentricMappingRigid(TObject):
	pass

class BeamLinearMapping(TObject):
	pass

class CenterOfMassMapping(TObject):
	pass

class CenterOfMassMulti2Mapping(TObject):
	pass

class CenterOfMassMultiMapping(TObject):
	pass

class DeformableOnRigidFrameMapping(TObject):
	pass

class IdentityMultiMapping(TObject):
	pass

class LineSetSkinningMapping(TObject):
	pass

class Mesh2PointMechanicalMapping(TObject):
	pass

class Mesh2PointTopologicalMapping(TObject):
	pass

class SimpleTesselatedHexaTopologicalMapping(TObject):
	pass

class SimpleTesselatedTetraMechanicalMapping(TObject):
	pass

class SimpleTesselatedTetraTopologicalMapping(TObject):
	pass

class SkinningMapping(TObject):
	pass

class SubsetMultiMapping(TObject):
	pass

class TopologyBarycentricMapper(TObject):
	pass

class TubularMapping(TObject):
	pass

class VoidMapping(TObject):
	pass

class ForceFeedback(TObject):
	pass

class LCPForceFeedback(TObject):
	pass

class NullForceFeedback(TObject):
	pass

class NullForceFeedbackT(TObject):
	pass

class TextureInterpolation(TObject):
	pass

class CompositingVisualLoop(TObject):
	pass

class Light(TObject):
	pass

class LightManager(TObject):
	pass

class OglAttribute(TObject):
	pass

class OglOITShader(TObject):
	pass

class OglRenderingSRGB(TObject):
	pass

class OglShader(TObject):
	pass

class OglShaderMacro(TObject):
	pass

class OglShaderVisualModel(TObject):
	pass

class OglShadowShader(TObject):
	pass

class OglTexture(TObject):
	pass

class OglTexturePointer(TObject):
	pass

class OglVariable(TObject):
	pass

class OrderIndependentTransparencyManager(TObject):
	pass

class PostProcessManager(TObject):
	pass

class VisualManagerPass(TObject):
	pass

class VisualManagerSecondaryPass(TObject):
	pass

class OglColorMap(TObject):
	pass

class OglLabel(TObject):
	pass

class OglViewport(TObject):
	pass

class ClipPlane(TObject):
	pass

class DataDisplay(TObject):
	pass

class MergeVisualModels(TObject):
	pass

class OglModel(TObject):
	pass

class OglSceneFrame(TObject):
	pass

class PointSplatModel(TObject):
	pass

class SlicedVolumetricModel(TObject):
	pass

class Axis(TObject):
	pass

class BasicShapesGL(TObject):
	pass

class Capture(TObject):
	pass

class Cylinder(TObject):
	pass

class DrawToolGL(TObject):
	pass

class FrameBufferObject(TObject):
	pass

class GLSLShader(TObject):
	pass

class Texture(TObject):
	pass

class TransformationGL(TObject):
	pass

class VideoRecorderFFMPEG(TObject):
	pass

REQUIRED_PLUGINS = {
	"GlobalSystemMatrixExporter": "SofaMatrix",
	"MappedObject": "Sofa.Component.StateContainer",
	"MechanicalObject": "Sofa.Component.StateContainer",
	"ConstraintAnimationLoop": "Sofa.Component.AnimationLoop",
	"FreeMotionAnimationLoop": "Sofa.Component.AnimationLoop",
	"MultiStepAnimationLoop": "Sofa.Component.AnimationLoop",
	"MultiTagAnimationLoop": "Sofa.Component.AnimationLoop",
	"APIVersion": "Sofa.Component.SceneUtility",
	"AddResourceRepository": "Sofa.Component.SceneUtility",
	"InfoComponent": "Sofa.Component.SceneUtility",
	"MakeAliasComponent": "Sofa.Component.SceneUtility",
	"MakeDataAliasComponent": "Sofa.Component.SceneUtility",
	"MessageHandlerComponent": "Sofa.Component.SceneUtility",
	"PauseAnimation": "Sofa.Component.SceneUtility",
	"PauseAnimationOnEvent": "Sofa.Component.SceneUtility",
	"BaseProximityIntersection": "Sofa.Component.Collision.Detection.Intersection",
	"DiscreteIntersection": "Sofa.Component.Collision.Detection.Intersection",
	"LocalMinDistance": "Sofa.Component.Collision.Detection.Intersection",
	"MeshDiscreteIntersection": "Sofa.Component.Collision.Detection.Intersection",
	"MeshMinProximityIntersection": "Sofa.Component.Collision.Detection.Intersection",
	"MeshNewProximityIntersection": "Sofa.Component.Collision.Detection.Intersection",
	"MinProximityIntersection": "Sofa.Component.Collision.Detection.Intersection",
	"NewProximityIntersection": "Sofa.Component.Collision.Detection.Intersection",
	"RayDiscreteIntersection": "Sofa.Component.Collision.Detection.Intersection",
	"RayNewProximityIntersection": "Sofa.Component.Collision.Detection.Intersection",
	"TetrahedronDiscreteIntersection": "Sofa.Component.Collision.Detection.Intersection",
	"BVHNarrowPhase": "Sofa.Component.Collision.Detection.Algorithm",
	"BruteForceBroadPhase": "Sofa.Component.Collision.Detection.Algorithm",
	"BruteForceDetection": "Sofa.Component.Collision.Detection.Algorithm",
	"CollisionPipeline": "Sofa.Component.Collision.Detection.Algorithm",
	"DSAPBox": "Sofa.Component.Collision.Detection.Algorithm",
	"DirectSAP": "Sofa.Component.Collision.Detection.Algorithm",
	"DirectSAPNarrowPhase": "Sofa.Component.Collision.Detection.Algorithm",
	"IncrSAP": "Sofa.Component.Collision.Detection.Algorithm",
	"RayTraceDetection": "Sofa.Component.Collision.Detection.Algorithm",
	"RayTraceNarrowPhase": "Sofa.Component.Collision.Detection.Algorithm",
	"CubeModel": "Sofa.Component.Collision.Geometry",
	"CylinderModel": "Sofa.Component.Collision.Geometry",
	"LineModel": "Sofa.Component.Collision.Geometry",
	"PointModel": "Sofa.Component.Collision.Geometry",
	"PointCollisionModel": "Sofa.Component.Collision.Geometry",
	"RayModel": "Sofa.Component.Collision.Geometry",
	"SphereModel": "Sofa.Component.Collision.Geometry",
	"TetrahedronModel": "Sofa.Component.Collision.Geometry",
	"TriangleModel": "Sofa.Component.Collision.Geometry",
	"TriangleModelInRegularGrid": "Sofa.Component.Collision.Geometry",
	"TriangleOctreeModel": "Sofa.Component.Collision.Geometry",
	"BarycentricContactMapper": "Sofa.Component.Collision.Response.Mapper",
	"BaseContactMapper": "Sofa.Component.Collision.Response.Mapper",
	"IdentityContactMapper": "Sofa.Component.Collision.Response.Mapper",
	"RigidContactMapper": "Sofa.Component.Collision.Response.Mapper",
	"SubsetContactMapper": "Sofa.Component.Collision.Response.Mapper",
	"TetrahedronBarycentricContactMapper": "Sofa.Component.Collision.Response.Mapper",
	"AugmentedLagrangianResponse": "Sofa.Component.Collision.Response.Contact",
	"BarycentricPenalityContact": "Sofa.Component.Collision.Response.Contact",
	"BarycentricStickContact": "Sofa.Component.Collision.Response.Contact",
	"CollisionResponse": "Sofa.Component.Collision.Response.Contact",
	"ContactIdentifier": "Sofa.Component.Collision.Response.Contact",
	"ContactListener": "Sofa.Component.Collision.Response.Contact",
	"FrictionContact": "Sofa.Component.Collision.Response.Contact",
	"PenalityContactForceField": "Sofa.Component.Collision.Response.Contact",
	"RayContact": "Sofa.Component.Collision.Response.Contact",
	"RuleBasedContactManager": "Sofa.Component.Collision.Response.Contact",
	"StickContactConstraint": "Sofa.Component.Collision.Response.Contact",
	"TetrahedronAugmentedLagrangianContact": "Sofa.Component.Collision.Response.Contact",
	"TetrahedronBarycentricPenalityContact": "Sofa.Component.Collision.Response.Contact",
	"TetrahedronFrictionContact": "Sofa.Component.Collision.Response.Contact",
	"TetrahedronRayContact": "Sofa.Component.Collision.Response.Contact",
	"AffineMovementProjectiveConstraint": "Sofa.Component.Constraint.Projective",
	"AttachProjectiveConstraint": "Sofa.Component.Constraint.Projective",
	"DirectionProjectiveConstraint": "Sofa.Component.Constraint.Projective",
	"FixedPlaneProjectiveConstraint": "Sofa.Component.Constraint.Projective",
	"FixedProjectiveConstraint": "Sofa.Component.Constraint.Projective",
	"FixedRotationProjectiveConstraint": "Sofa.Component.Constraint.Projective",
	"FixedTranslationProjectiveConstraint": "Sofa.Component.Constraint.Projective",
	"HermiteSplineProjectiveConstraint": "Sofa.Component.Constraint.Projective",
	"LineProjectiveConstraint": "Sofa.Component.Constraint.Projective",
	"LinearMovementProjectiveConstraint": "Sofa.Component.Constraint.Projective",
	"LinearVelocityProjectiveConstraint": "Sofa.Component.Constraint.Projective",
	"OscillatorProjectiveConstraint": "Sofa.Component.Constraint.Projective",
	"ParabolicProjectiveConstraint": "Sofa.Component.Constraint.Projective",
	"PartialFixedProjectiveConstraint": "Sofa.Component.Constraint.Projective",
	"PartialLinearMovementProjectiveConstraint": "Sofa.Component.Constraint.Projective",
	"PatchTestMovementProjectiveConstraint": "Sofa.Component.Constraint.Projective",
	"PlaneProjectiveConstraint": "Sofa.Component.Constraint.Projective",
	"PointProjectiveConstraint": "Sofa.Component.Constraint.Projective",
	"PositionBasedDynamicsProjectiveConstraint": "Sofa.Component.Constraint.Projective",
	"SkeletalMotionProjectiveConstraint": "Sofa.Component.Constraint.Projective",
	"AugmentedLagrangianConstraint": "Sofa.Component.Constraint.Lagrangian.Model",
	"BilateralLagrangianConstraint": "Sofa.Component.Constraint.Lagrangian.Model",
	"FixedLagrangianConstraint": "Sofa.Component.Constraint.Lagrangian.Model",
	"SlidingLagrangianConstraint": "Sofa.Component.Constraint.Lagrangian.Model",
	"StopperLagrangianConstraint": "Sofa.Component.Constraint.Lagrangian.Model",
	"UniformLagrangianConstraint": "Sofa.Component.Constraint.Lagrangian.Model",
	"UnilateralLagrangianConstraint": "Sofa.Component.Constraint.Lagrangian.Model",
	"ConstraintSolverImpl": "Sofa.Component.Constraint.Lagrangian.Solver",
	"ConstraintStoreLambdaVisitor": "Sofa.Component.Constraint.Lagrangian.Solver",
	"GenericConstraintProblem": "Sofa.Component.Constraint.Lagrangian.Solver",
	"GenericConstraintSolver": "Sofa.Component.Constraint.Lagrangian.Solver",
	"LCPConstraintSolver": "Sofa.Component.Constraint.Lagrangian.Solver",
	"MechanicalGetConstraintResolutionVisitor": "Sofa.Component.Constraint.Lagrangian.Solver",
	"MechanicalGetConstraintViolationVisitor": "Sofa.Component.Constraint.Lagrangian.Solver",
	"GenericConstraintCorrection": "Sofa.Component.Constraint.Lagrangian.Correction",
	"LinearSolverConstraintCorrection": "Sofa.Component.Constraint.Lagrangian.Correction",
	"PrecomputedConstraintCorrection": "Sofa.Component.Constraint.Lagrangian.Correction",
	"UncoupledConstraintCorrection": "Sofa.Component.Constraint.Lagrangian.Correction",
	"DifferenceEngine": "Sofa.Component.Engine.Transform",
	"DilateEngine": "Sofa.Component.Engine.Transform",
	"DisplacementMatrixEngine": "Sofa.Component.Engine.Transform",
	"IndexValueMapper": "Sofa.Component.Engine.Transform",
	"Indices2ValuesMapper": "Sofa.Component.Engine.Transform",
	"MapIndices": "Sofa.Component.Engine.Transform",
	"MathOp": "Sofa.Component.Engine.Transform",
	"ProjectiveTransformEngine": "Sofa.Component.Engine.Transform",
	"QuatToRigidEngine": "Sofa.Component.Engine.Transform",
	"ROIValueMapper": "Sofa.Component.Engine.Transform",
	"RigidToQuatEngine": "Sofa.Component.Engine.Transform",
	"SmoothMeshEngine": "Sofa.Component.Engine.Transform",
	"TransformEngine": "Sofa.Component.Engine.Transform",
	"TransformMatrixEngine": "Sofa.Component.Engine.Transform",
	"TransformPosition": "Sofa.Component.Engine.Transform",
	"Vertex2Frame": "Sofa.Component.Engine.Transform",
	"BoxROI": "Sofa.Component.Engine.Select",
	"ComplementaryROI": "Sofa.Component.Engine.Select",
	"IndicesFromValues": "Sofa.Component.Engine.Select",
	"MergeROIs": "Sofa.Component.Engine.Select",
	"MeshBoundaryROI": "Sofa.Component.Engine.Select",
	"MeshROI": "Sofa.Component.Engine.Select",
	"MeshSampler": "Sofa.Component.Engine.Select",
	"MeshSplittingEngine": "Sofa.Component.Engine.Select",
	"MeshSubsetEngine": "Sofa.Component.Engine.Select",
	"NearestPointROI": "Sofa.Component.Engine.Select",
	"PairBoxRoi": "Sofa.Component.Engine.Select",
	"PlaneROI": "Sofa.Component.Engine.Select",
	"PointsFromIndices": "Sofa.Component.Engine.Select",
	"ProximityROI": "Sofa.Component.Engine.Select",
	"SelectConnectedLabelsROI": "Sofa.Component.Engine.Select",
	"SelectLabelROI": "Sofa.Component.Engine.Select",
	"SphereROI": "Sofa.Component.Engine.Select",
	"SubsetTopology": "Sofa.Component.Engine.Select",
	"ValuesFromIndices": "Sofa.Component.Engine.Select",
	"ValuesFromPositions": "Sofa.Component.Engine.Select",
	"AverageCoord": "Sofa.Component.Engine.Analyze",
	"ClusteringEngine": "Sofa.Component.Engine.Analyze",
	"Distances": "Sofa.Component.Engine.Analyze",
	"HausdorffDistance": "Sofa.Component.Engine.Analyze",
	"ShapeMatching": "Sofa.Component.Engine.Analyze",
	"SumEngine": "Sofa.Component.Engine.Analyze",
	"ExtrudeEdgesAndGenerateQuads": "Sofa.Component.Engine.Generate",
	"ExtrudeQuadsAndGenerateHexas": "Sofa.Component.Engine.Generate",
	"ExtrudeSurface": "Sofa.Component.Engine.Generate",
	"GenerateCylinder": "Sofa.Component.Engine.Generate",
	"GenerateGrid": "Sofa.Component.Engine.Generate",
	"GenerateRigidMass": "Sofa.Component.Engine.Generate",
	"GenerateSphere": "Sofa.Component.Engine.Generate",
	"GroupFilterYoungModulus": "Sofa.Component.Engine.Generate",
	"JoinPoints": "Sofa.Component.Engine.Generate",
	"MergeMeshes": "Sofa.Component.Engine.Generate",
	"MergePoints": "Sofa.Component.Engine.Generate",
	"MergeSets": "Sofa.Component.Engine.Generate",
	"MergeVectors": "Sofa.Component.Engine.Generate",
	"MeshBarycentricMapperEngine": "Sofa.Component.Engine.Generate",
	"MeshClosingEngine": "Sofa.Component.Engine.Generate",
	"MeshTetraStuffing": "Sofa.Component.Engine.Generate",
	"NormEngine": "Sofa.Component.Engine.Generate",
	"NormalsFromPoints": "Sofa.Component.Engine.Generate",
	"RandomPointDistributionInSurface": "Sofa.Component.Engine.Generate",
	"Spiral": "Sofa.Component.Engine.Generate",
	"BackgroundSetting": "Sofa.Component.Setting",
	"MouseButtonSetting": "Sofa.Component.Setting",
	"SofaDefaultPathSetting": "Sofa.Component.Setting",
	"StatsSetting": "Sofa.Component.Setting",
	"ViewerSetting": "Sofa.Component.Setting",
	"AMDOrderingMethod": "Sofa.Component.LinearSolver.Ordering",
	"COLAMDOrderingMethod": "Sofa.Component.LinearSolver.Ordering",
	"NaturalOrderingMethod": "Sofa.Component.LinearSolver.Ordering",
	"CGLinearSolver": "Sofa.Component.LinearSolver.Iterative",
	"GraphScatteredTypes": "Sofa.Component.LinearSolver.Iterative",
	"LinearSystemData": "Sofa.Component.LinearSolver.Iterative",
	"MatrixFreeSystem": "Sofa.Component.LinearSolver.Iterative",
	"MatrixLinearSolver": "Sofa.Component.LinearSolver.Iterative",
	"MatrixLinearSystem": "Sofa.Component.LinearSolver.Iterative",
	"MinResLinearSolver": "Sofa.Component.LinearSolver.Iterative",
	"PCGLinearSolver": "Sofa.Component.LinearSolver.Iterative",
	"AsyncSparseLDLSolver": "Sofa.Component.LinearSolver.Direct",
	"BTDLinearSolver": "Sofa.Component.LinearSolver.Direct",
	"CholeskySolver": "Sofa.Component.LinearSolver.Direct",
	"EigenSimplicialLDLT": "Sofa.Component.LinearSolver.Direct",
	"EigenSimplicialLLT": "Sofa.Component.LinearSolver.Direct",
	"EigenSolverFactory": "Sofa.Component.LinearSolver.Direct",
	"EigenSparseLU": "Sofa.Component.LinearSolver.Direct",
	"EigenSparseQR": "Sofa.Component.LinearSolver.Direct",
	"MatrixLinearSystem": "Sofa.Component.LinearSolver.Direct",
	"PrecomputedLinearSolver": "Sofa.Component.LinearSolver.Direct",
	"SVDLinearSolver": "Sofa.Component.LinearSolver.Direct",
	"SparseCommon": "Sofa.Component.LinearSolver.Direct",
	"SparseLDLSolver": "Sofa.Component.LinearSolver.Direct",
	"TypedMatrixLinearSystem": "Sofa.Component.LinearSolver.Direct",
	"BlockJacobiPreconditioner": "Sofa.Component.LinearSolver.Preconditioner",
	"JacobiPreconditioner": "Sofa.Component.LinearSolver.Preconditioner",
	"PrecomputedMatrixSystem": "Sofa.Component.LinearSolver.Preconditioner",
	"PrecomputedWarpPreconditioner": "Sofa.Component.LinearSolver.Preconditioner",
	"RotationMatrixSystem": "Sofa.Component.LinearSolver.Preconditioner",
	"SSORPreconditioner": "Sofa.Component.LinearSolver.Preconditioner",
	"WarpPreconditioner": "Sofa.Component.LinearSolver.Preconditioner",
	"ConicalForceField": "Sofa.Component.MechanicalLoad",
	"ConstantForceField": "Sofa.Component.MechanicalLoad",
	"DiagonalVelocityDampingForceField": "Sofa.Component.MechanicalLoad",
	"EdgePressureForceField": "Sofa.Component.MechanicalLoad",
	"EllipsoidForceField": "Sofa.Component.MechanicalLoad",
	"Gravity": "Sofa.Component.MechanicalLoad",
	"InteractionEllipsoidForceField": "Sofa.Component.MechanicalLoad",
	"LinearForceField": "Sofa.Component.MechanicalLoad",
	"OscillatingTorsionPressureForceField": "Sofa.Component.MechanicalLoad",
	"PlaneForceField": "Sofa.Component.MechanicalLoad",
	"QuadPressureForceField": "Sofa.Component.MechanicalLoad",
	"SphereForceField": "Sofa.Component.MechanicalLoad",
	"SurfacePressureForceField": "Sofa.Component.MechanicalLoad",
	"TaitSurfacePressureForceField": "Sofa.Component.MechanicalLoad",
	"TorsionForceField": "Sofa.Component.MechanicalLoad",
	"TrianglePressureForceField": "Sofa.Component.MechanicalLoad",
	"UniformVelocityDampingForceField": "Sofa.Component.MechanicalLoad",
	"BaseCamera": "Sofa.Component.Visual",
	"Camera": "Sofa.Component.Visual",
	"CylinderVisualModel": "Sofa.Component.Visual",
	"InteractiveCamera": "Sofa.Component.Visual",
	"LineAxis": "Sofa.Component.Visual",
	"RecordedCamera": "Sofa.Component.Visual",
	"TrailRenderer": "Sofa.Component.Visual",
	"Visual3DText": "Sofa.Component.Visual",
	"VisualGrid": "Sofa.Component.Visual",
	"VisualModelImpl": "Sofa.Component.Visual",
	"VisualStyle": "Sofa.Component.Visual",
	"VisualTransform": "Sofa.Component.Visual",
	"CentralDifferenceSolver": "Sofa.Component.ODESolver.Forward",
	"DampVelocitySolver": "Sofa.Component.ODESolver.Forward",
	"EulerExplicitSolver": "Sofa.Component.ODESolver.Forward",
	"RungeKutta2Solver": "Sofa.Component.ODESolver.Forward",
	"RungeKutta4Solver": "Sofa.Component.ODESolver.Forward",
	"EulerImplicitSolver": "Sofa.Component.ODESolver.Backward",
	"NewmarkImplicitSolver": "Sofa.Component.ODESolver.Backward",
	"StaticSolver": "Sofa.Component.ODESolver.Backward",
	"VariationalSymplecticSolver": "Sofa.Component.ODESolver.Backward",
	"CompareState": "Sofa.Component.Playback",
	"CompareTopology": "Sofa.Component.Playback",
	"InputEventReader": "Sofa.Component.Playback",
	"ReadState": "Sofa.Component.Playback",
	"ReadTopology": "Sofa.Component.Playback",
	"WriteState": "Sofa.Component.Playback",
	"WriteTopology": "Sofa.Component.Playback",
	"Controller": "Sofa.Component.Controller",
	"MechanicalStateController": "Sofa.Component.Controller",
	"TetrahedronDiffusionFEMForceField": "Sofa.Component.Diffusion",
	"AngularSpringForceField": "Sofa.Component.SolidMechanics.Spring",
	"FastTriangularBendingSprings": "Sofa.Component.SolidMechanics.Spring",
	"FrameSpringForceField": "Sofa.Component.SolidMechanics.Spring",
	"GearSpringForceField": "Sofa.Component.SolidMechanics.Spring",
	"JointSpring": "Sofa.Component.SolidMechanics.Spring",
	"JointSpringForceField": "Sofa.Component.SolidMechanics.Spring",
	"LinearSpring": "Sofa.Component.SolidMechanics.Spring",
	"MeshSpringForceField": "Sofa.Component.SolidMechanics.Spring",
	"PolynomialRestShapeSpringsForceField": "Sofa.Component.SolidMechanics.Spring",
	"PolynomialSpringsForceField": "Sofa.Component.SolidMechanics.Spring",
	"QuadBendingSprings": "Sofa.Component.SolidMechanics.Spring",
	"QuadularBendingSprings": "Sofa.Component.SolidMechanics.Spring",
	"RegularGridSpringForceField": "Sofa.Component.SolidMechanics.Spring",
	"RepulsiveSpringForceField": "Sofa.Component.SolidMechanics.Spring",
	"RestShapeSpringsForceField": "Sofa.Component.SolidMechanics.Spring",
	"SpringForceField": "Sofa.Component.SolidMechanics.Spring",
	"TriangleBendingSprings": "Sofa.Component.SolidMechanics.Spring",
	"TriangularBendingSprings": "Sofa.Component.SolidMechanics.Spring",
	"TriangularBiquadraticSpringsForceField": "Sofa.Component.SolidMechanics.Spring",
	"TriangularQuadraticSpringsForceField": "Sofa.Component.SolidMechanics.Spring",
	"VectorSpringForceField": "Sofa.Component.SolidMechanics.Spring",
	"TetrahedralTensorMassForceField": "Sofa.Component.SolidMechanics.TensorMass",
	"TriangularTensorMassForceField": "Sofa.Component.SolidMechanics.TensorMass",
	"PlasticMaterial": "Sofa.Component.SolidMechanics.FEM.HyperElastic",
	"StandardTetrahedralFEMForceField": "Sofa.Component.SolidMechanics.FEM.HyperElastic",
	"TetrahedronHyperelasticityFEMForceField": "Sofa.Component.SolidMechanics.FEM.HyperElastic",
	"BaseLinearElasticityFEMForceField": "Sofa.Component.SolidMechanics.FEM.Elastic",
	"BeamFEMForceField": "Sofa.Component.SolidMechanics.FEM.Elastic",
	"FastTetrahedralCorotationalForceField": "Sofa.Component.SolidMechanics.FEM.Elastic",
	"HexahedralFEMForceField": "Sofa.Component.SolidMechanics.FEM.Elastic",
	"HexahedralFEMForceFieldAndMass": "Sofa.Component.SolidMechanics.FEM.Elastic",
	"HexahedronFEMForceField": "Sofa.Component.SolidMechanics.FEM.Elastic",
	"HexahedronFEMForceFieldAndMass": "Sofa.Component.SolidMechanics.FEM.Elastic",
	"QuadBendingFEMForceField": "Sofa.Component.SolidMechanics.FEM.Elastic",
	"TetrahedralCorotationalFEMForceField": "Sofa.Component.SolidMechanics.FEM.Elastic",
	"TetrahedronFEMForceField": "Sofa.Component.SolidMechanics.FEM.Elastic",
	"TriangleFEMForceField": "Sofa.Component.SolidMechanics.FEM.Elastic",
	"TriangleFEMUtils": "Sofa.Component.SolidMechanics.FEM.Elastic",
	"TriangularAnisotropicFEMForceField": "Sofa.Component.SolidMechanics.FEM.Elastic",
	"TriangularFEMForceField": "Sofa.Component.SolidMechanics.FEM.Elastic",
	"TriangularFEMForceFieldOptim": "Sofa.Component.SolidMechanics.FEM.Elastic",
	"HexahedronCompositeFEMForceFieldAndMass": "Sofa.Component.SolidMechanics.FEM.NonUniform",
	"HexahedronCompositeFEMMapping": "Sofa.Component.SolidMechanics.FEM.NonUniform",
	"NonUniformHexahedralFEMForceFieldAndMass": "Sofa.Component.SolidMechanics.FEM.NonUniform",
	"NonUniformHexahedronFEMForceFieldAndMass": "Sofa.Component.SolidMechanics.FEM.NonUniform",
	"AffinePatch_test": "Sofa.Component.SolidMechanics_simutest",
	"LinearElasticity_test": "Sofa.Component.SolidMechanics_simutest",
	"BaseVTKReader": "Sofa.Component.IO.Mesh",
	"BlenderExporter": "Sofa.Component.IO.Mesh",
	"GIDMeshLoader": "Sofa.Component.IO.Mesh",
	"GridMeshCreator": "Sofa.Component.IO.Mesh",
	"MeshExporter": "Sofa.Component.IO.Mesh",
	"MeshGmshLoader": "Sofa.Component.IO.Mesh",
	"MeshOBJLoader": "Sofa.Component.IO.Mesh",
	"MeshOffLoader": "Sofa.Component.IO.Mesh",
	"MeshSTLLoader": "Sofa.Component.IO.Mesh",
	"MeshTrianLoader": "Sofa.Component.IO.Mesh",
	"MeshVTKLoader": "Sofa.Component.IO.Mesh",
	"MeshXspLoader": "Sofa.Component.IO.Mesh",
	"OffSequenceLoader": "Sofa.Component.IO.Mesh",
	"STLExporter": "Sofa.Component.IO.Mesh",
	"SphereLoader": "Sofa.Component.IO.Mesh",
	"StringMeshCreator": "Sofa.Component.IO.Mesh",
	"VTKExporter": "Sofa.Component.IO.Mesh",
	"VisualModelOBJExporter": "Sofa.Component.IO.Mesh",
	"VoxelGridLoader": "Sofa.Component.IO.Mesh",
	"AssembleGlobalVectorFromLocalVectorVisitor": "Sofa.Component.LinearSystem",
	"BaseMatrixProjectionMethod": "Sofa.Component.LinearSystem",
	"CompositeLinearSystem": "Sofa.Component.LinearSystem",
	"ConstantSparsityPatternSystem": "Sofa.Component.LinearSystem",
	"ConstantSparsityProjectionMethod": "Sofa.Component.LinearSystem",
	"DispatchFromGlobalVectorToLocalVectorVisitor": "Sofa.Component.LinearSystem",
	"MappedMassMatrixObserver": "Sofa.Component.LinearSystem",
	"MappingGraph": "Sofa.Component.LinearSystem",
	"MatrixLinearSystem": "Sofa.Component.LinearSystem",
	"MatrixProjectionMethod": "Sofa.Component.LinearSystem",
	"TypedMatrixLinearSystem": "Sofa.Component.LinearSystem",
	"TopologicalChangeProcessor": "Sofa.Component.Topology.Utility",
	"TopologyBoundingTrasher": "Sofa.Component.Topology.Utility",
	"TopologyChecker": "Sofa.Component.Topology.Utility",
	"CylinderGridTopology": "Sofa.Component.Topology.Container.Grid",
	"GridTopology": "Sofa.Component.Topology.Container.Grid",
	"RegularGridTopology": "Sofa.Component.Topology.Container.Grid",
	"SparseGridMultipleTopology": "Sofa.Component.Topology.Container.Grid",
	"SparseGridRamificationTopology": "Sofa.Component.Topology.Container.Grid",
	"SparseGridTopology": "Sofa.Component.Topology.Container.Grid",
	"SphereGridTopology": "Sofa.Component.Topology.Container.Grid",
	"CubeTopology": "Sofa.Component.Topology.Container.Constant",
	"MeshTopology": "Sofa.Component.Topology.Container.Constant",
	"SphereQuadTopology": "Sofa.Component.Topology.Container.Constant",
	"DynamicSparseGridGeometryAlgorithms": "Sofa.Component.Topology.Container.Dynamic",
	"DynamicSparseGridTopologyContainer": "Sofa.Component.Topology.Container.Dynamic",
	"DynamicSparseGridTopologyModifier": "Sofa.Component.Topology.Container.Dynamic",
	"EdgeSetGeometryAlgorithms": "Sofa.Component.Topology.Container.Dynamic",
	"EdgeSetTopologyContainer": "Sofa.Component.Topology.Container.Dynamic",
	"EdgeSetTopologyModifier": "Sofa.Component.Topology.Container.Dynamic",
	"HexahedronSetGeometryAlgorithms": "Sofa.Component.Topology.Container.Dynamic",
	"HexahedronSetTopologyContainer": "Sofa.Component.Topology.Container.Dynamic",
	"HexahedronSetTopologyModifier": "Sofa.Component.Topology.Container.Dynamic",
	"MultilevelHexahedronSetTopologyContainer": "Sofa.Component.Topology.Container.Dynamic",
	"NumericalIntegrationDescriptor": "Sofa.Component.Topology.Container.Dynamic",
	"PointSetGeometryAlgorithms": "Sofa.Component.Topology.Container.Dynamic",
	"PointSetTopologyContainer": "Sofa.Component.Topology.Container.Dynamic",
	"PointSetTopologyModifier": "Sofa.Component.Topology.Container.Dynamic",
	"QuadSetGeometryAlgorithms": "Sofa.Component.Topology.Container.Dynamic",
	"QuadSetTopologyContainer": "Sofa.Component.Topology.Container.Dynamic",
	"QuadSetTopologyModifier": "Sofa.Component.Topology.Container.Dynamic",
	"TetrahedronSetGeometryAlgorithms": "Sofa.Component.Topology.Container.Dynamic",
	"TetrahedronSetTopologyContainer": "Sofa.Component.Topology.Container.Dynamic",
	"TetrahedronSetTopologyModifier": "Sofa.Component.Topology.Container.Dynamic",
	"TriangleSetGeometryAlgorithms": "Sofa.Component.Topology.Container.Dynamic",
	"TriangleSetTopologyContainer": "Sofa.Component.Topology.Container.Dynamic",
	"TriangleSetTopologyModifier": "Sofa.Component.Topology.Container.Dynamic",
	"CenterPointTopologicalMapping": "Sofa.Component.Topology.Mapping",
	"Edge2QuadTopologicalMapping": "Sofa.Component.Topology.Mapping",
	"Hexa2QuadTopologicalMapping": "Sofa.Component.Topology.Mapping",
	"Hexa2TetraTopologicalMapping": "Sofa.Component.Topology.Mapping",
	"IdentityTopologicalMapping": "Sofa.Component.Topology.Mapping",
	"Quad2TriangleTopologicalMapping": "Sofa.Component.Topology.Mapping",
	"SubsetTopologicalMapping": "Sofa.Component.Topology.Mapping",
	"Tetra2TriangleTopologicalMapping": "Sofa.Component.Topology.Mapping",
	"Triangle2EdgeTopologicalMapping": "Sofa.Component.Topology.Mapping",
	"DiagonalMass": "Sofa.Component.Mass",
	"MeshMatrixMass": "Sofa.Component.Mass",
	"UniformMass": "Sofa.Component.Mass",
	"AreaMapping": "Sofa.Component.Mapping.NonLinear",
	"DistanceFromTargetMapping": "Sofa.Component.Mapping.NonLinear",
	"DistanceMapping": "Sofa.Component.Mapping.NonLinear",
	"DistanceMultiMapping": "Sofa.Component.Mapping.NonLinear",
	"RigidMapping": "Sofa.Component.Mapping.NonLinear",
	"SquareDistanceMapping": "Sofa.Component.Mapping.NonLinear",
	"SquareMapping": "Sofa.Component.Mapping.NonLinear",
	"VolumeMapping": "Sofa.Component.Mapping.NonLinear",
	"BarycentricMapper": "Sofa.Component.Mapping.Linear",
	"BarycentricMapperEdgeSetTopology": "Sofa.Component.Mapping.Linear",
	"BarycentricMapperHexahedronSetTopology": "Sofa.Component.Mapping.Linear",
	"BarycentricMapperMeshTopology": "Sofa.Component.Mapping.Linear",
	"BarycentricMapperQuadSetTopology": "Sofa.Component.Mapping.Linear",
	"BarycentricMapperRegularGridTopology": "Sofa.Component.Mapping.Linear",
	"BarycentricMapperSparseGridTopology": "Sofa.Component.Mapping.Linear",
	"BarycentricMapperTetrahedronSetTopology": "Sofa.Component.Mapping.Linear",
	"BarycentricMapperTopologyContainer": "Sofa.Component.Mapping.Linear",
	"BarycentricMapperTriangleSetTopology": "Sofa.Component.Mapping.Linear",
	"BarycentricMapping": "Sofa.Component.Mapping.Linear",
	"BarycentricMappingRigid": "Sofa.Component.Mapping.Linear",
	"BeamLinearMapping": "Sofa.Component.Mapping.Linear",
	"CenterOfMassMapping": "Sofa.Component.Mapping.Linear",
	"CenterOfMassMulti2Mapping": "Sofa.Component.Mapping.Linear",
	"CenterOfMassMultiMapping": "Sofa.Component.Mapping.Linear",
	"DeformableOnRigidFrameMapping": "Sofa.Component.Mapping.Linear",
	"IdentityMapping": "Sofa.Component.Mapping.Linear",
	"IdentityMultiMapping": "Sofa.Component.Mapping.Linear",
	"LineSetSkinningMapping": "Sofa.Component.Mapping.Linear",
	"Mesh2PointMechanicalMapping": "Sofa.Component.Mapping.Linear",
	"Mesh2PointTopologicalMapping": "Sofa.Component.Mapping.Linear",
	"SimpleTesselatedHexaTopologicalMapping": "Sofa.Component.Mapping.Linear",
	"SimpleTesselatedTetraMechanicalMapping": "Sofa.Component.Mapping.Linear",
	"SimpleTesselatedTetraTopologicalMapping": "Sofa.Component.Mapping.Linear",
	"SkinningMapping": "Sofa.Component.Mapping.Linear",
	"SubsetMapping": "Sofa.Component.Mapping.Linear",
	"SubsetMultiMapping": "Sofa.Component.Mapping.Linear",
	"TopologyBarycentricMapper": "Sofa.Component.Mapping.Linear",
	"TubularMapping": "Sofa.Component.Mapping.Linear",
	"VoidMapping": "Sofa.Component.Mapping.Linear",
	"ForceFeedback": "Sofa.Component.Haptics",
	"LCPForceFeedback": "Sofa.Component.Haptics",
	"NullForceFeedback": "Sofa.Component.Haptics",
	"NullForceFeedbackT": "Sofa.Component.Haptics",
	"TextureInterpolation": "Sofa.GL.Component.Engine",
	"CompositingVisualLoop": "Sofa.GL.Component.Shader",
	"Light": "Sofa.GL.Component.Shader",
	"LightManager": "Sofa.GL.Component.Shader",
	"OglAttribute": "Sofa.GL.Component.Shader",
	"OglOITShader": "Sofa.GL.Component.Shader",
	"OglRenderingSRGB": "Sofa.GL.Component.Shader",
	"OglShader": "Sofa.GL.Component.Shader",
	"OglShaderMacro": "Sofa.GL.Component.Shader",
	"OglShaderVisualModel": "Sofa.GL.Component.Shader",
	"OglShadowShader": "Sofa.GL.Component.Shader",
	"OglTexture": "Sofa.GL.Component.Shader",
	"OglTexturePointer": "Sofa.GL.Component.Shader",
	"OglVariable": "Sofa.GL.Component.Shader",
	"OrderIndependentTransparencyManager": "Sofa.GL.Component.Shader",
	"PostProcessManager": "Sofa.GL.Component.Shader",
	"VisualManagerPass": "Sofa.GL.Component.Shader",
	"VisualManagerSecondaryPass": "Sofa.GL.Component.Shader",
	"OglColorMap": "Sofa.GL.Component.Rendering2D",
	"OglLabel": "Sofa.GL.Component.Rendering2D",
	"OglViewport": "Sofa.GL.Component.Rendering2D",
	"ClipPlane": "Sofa.GL.Component.Rendering3D",
	"DataDisplay": "Sofa.GL.Component.Rendering3D",
	"MergeVisualModels": "Sofa.GL.Component.Rendering3D",
	"OglModel": "Sofa.GL.Component.Rendering3D",
	"OglSceneFrame": "Sofa.GL.Component.Rendering3D",
	"PointSplatModel": "Sofa.GL.Component.Rendering3D",
	"SlicedVolumetricModel": "Sofa.GL.Component.Rendering3D",
	"Axis": "Sofa.GL",
	"BasicShapesGL": "Sofa.GL",
	"Capture": "Sofa.GL",
	"Cylinder": "Sofa.GL",
	"DrawToolGL": "Sofa.GL",
	"FrameBufferObject": "Sofa.GL",
	"GLSLShader": "Sofa.GL",
	"Texture": "Sofa.GL",
	"TransformationGL": "Sofa.GL",
	"VideoRecorderFFMPEG": "Sofa.GL",
}
