from pydantic import BaseModel, Field
from typing import List, Dict, Literal, Union, Optional, Tuple
from steam_sdk.data.DataRoxieParser import RoxieData

## different to FiQuS
class MultipoleRoxieGeometry(BaseModel):
    """
        Class for FiQuS multipole Roxie data (.geom)
    """
    Roxie_Data: RoxieData = RoxieData()

## same as in FiQuS
class MultipoleGeoElement(BaseModel):
    """
    Level 5: Class for FiQuS Multipole
    """
    lines: Optional[int] = Field(
        default=3,
        description="It specifies the number of Gaussian points for lines.",
    )
    triangles: Optional[Literal[1, 3, 4, 6, 7, 12, 13, 16]] = Field(
        default=3,
        description="It specifies the number of Gaussian points for triangles.",
    )
    quadrangles: Optional[Literal[1, 3, 4, 7]] = Field(
        default=4,
        description="It specifies the number of Gaussian points for quadrangles.",
    )


class MultipoleSolveConvectionBoundaryCondition(BaseModel):
    """
    Level 5: Class for FiQuS Multipole
    """
    boundaries: Optional[List[str]] = Field(
        default=[],
        description="It specifies the list of boundaries where the condition is applied."
                    "Each boundary is identified by a string of the form <half-turn/wedge reference number><side>,"
                    "where the accepted sides are i, o, l, h which correspond respectively to inner, outer, lower (angle), higher (angle): e.g., 1o",
    )
    heat_transfer_coefficient: Optional[Union[float, str]] = Field(
        default=None,
        description="It specifies the value or function name of the heat transfer coefficient for this boundary condition.",
    )


class MultipoleSolveHeatFluxBoundaryCondition(BaseModel):
    """
    Level 5: Class for FiQuS Multipole
    """
    boundaries: Optional[List[str]] = Field(
        default=[],
        description="It specifies the list of boundaries where the condition is applied."
                    "Each boundary is identified by a string of the form <half-turn/wedge reference number><side>,"
                    "where the accepted sides are i, o, l, h which correspond respectively to inner, outer, lower (angle), higher (angle): e.g., 1o",
    )
    const_heat_flux: Optional[float] = Field(
        default=None,
        description="It specifies the value of the heat flux for this boundary condition.",
    )
    # function_heat_flux: Optional[str] = None


class MultipoleSolveTemperatureBoundaryCondition(BaseModel):
    """
    Level 5: Class for FiQuS Multipole
    """
    boundaries: Optional[List[str]] = Field(
        default=[],
        description="It specifies the list of boundaries where the condition is applied."
                    "Each boundary is identified by a string of the form <half-turn/wedge reference number><side>,"
                    "where the accepted sides are i, o, l, h which correspond respectively to inner, outer, lower (angle), higher (angle): e.g., 1o",
    )
    const_temperature: Optional[float] = Field(
        default=None,
        description="It specifies the value of the temperature for this boundary condition.",
    )
    # function_temperature: Optional[str] = None


class MultipoleSolveQuenchInitiation(BaseModel):
    """
    Level 4: Class for FiQuS Multipole
    """
    turns: Optional[List[int]] = Field(
        default=[],
        description="It specifies the list of reference numbers of half-turns whose critical currents are set to zero.",
    )
    t_trigger: Optional[List[float]] = Field(
        default=[],
        description="It specifies the list of time instants at which the critical current is set to zero.",
    )


class MultipoleSolveBoundaryConditionsThermal(BaseModel):
    """
    Level 4: Class for FiQuS Multipole
    """
    temperature: Optional[Dict[str, MultipoleSolveTemperatureBoundaryCondition]] = Field(
        default={},
        description="This dictionary contains the information about the Dirichlet boundary conditions."
                    "The keys are chosen names for each boundary condition.",
    )
    heat_flux: Optional[Dict[str, MultipoleSolveHeatFluxBoundaryCondition]] = Field(
        default={},
        description="This dictionary contains the information about the Neumann boundary conditions."
                    "The keys are chosen names for each boundary condition.",
    )
    cooling: Optional[Dict[str, MultipoleSolveConvectionBoundaryCondition]] = Field(
        default={},
        description="This dictionary contains the information about the Robin boundary conditions."
                    "The keys are chosen names for each boundary condition.",
    )

class MultipoleSolveTransient_parent(BaseModel):
    """
    Level 4: Class for FiQuS Multipole
    """
    initial_time: Optional[float] = Field(
        default=0.,
        description="It specifies the initial time of the simulation.",
    )
    final_time: Optional[float] = Field(
        default=0.0,
        description="It specifies the final time of the simulation.",
    )
    initial_time_step: Optional[float] = Field(
        default=1E-10,
        description="It specifies the initial time step used at the beginning of the transient simulation.",
    )
    min_time_step: Optional[float] = Field(
        default=1E-12,
        description="It specifies the minimum possible value of the time step.",
    )
    max_time_step: Optional[float] = Field(
        default=10,
        description="It specifies the maximum possible value of the time step.",
    )
    breakpoints: Optional[List[float]] = Field(
        default=[],
        description="It forces the transient simulation to hit the time instants contained in this list.",
    )
    integration_method: Optional[Union[None, Literal[
        "Euler", "Gear_2", "Gear_3", "Gear_4", "Gear_5", "Gear_6"
    ]]] = Field(
        default="Euler",
        title="Integration Method",
        description="It specifies the type of integration method to be used.",
    )
    rel_tol_time: Optional[float] = Field(
        default=1E-4,
        description="It specifies the relative tolerance.",
    )
    abs_tol_time: Optional[float] = Field(
        default=1e-4,
        description="It specifies the absolute tolerance.",
    )
    norm_type: Optional[Literal["L1Norm", "MeanL1Norm", "L2Norm", "MeanL2Norm", "LinfNorm"]] = Field(
        default='LinfNorm',
        description="It specifies the type of norm to be calculated for convergence assessment.",
    )

class MultipoleSolveTransientElectromagnetics(MultipoleSolveTransient_parent):
    """
    Level 4: Class for FiQuS Multipole
    """
    T_sim: Optional[float] = Field(
        default=1.9,
        description="It specifies the temperature used to calculate the resistivity of the superconductor during the transient sim.",
    )

class MultipleSolveCollarHeCooling(BaseModel):
    enabled: Optional[bool] = Field(
        default=False,
        description="It determines whether the helium cooling is enabled or not (adiabatic conditions).",
    )
    which: Optional[Union[Literal['all'], List]] = Field(
        default='all',
        description="It specifies the boundaries where the collar cooling is applied. If 'all', it applies to all boundaries. If a list, it applies to the specified boundaries numbered counter-clockwise."
    )
    heat_transfer_coefficient: Optional[Union[float, str]] = Field(
        default= 'CFUN_hHe_T_THe',
        description="It specifies the value or name of the function of the constant heat transfer coefficient.",
    )
    ref_temperature: Optional[float] = Field(
        default = 0.0,
        description="It specifies the reference temperature for the collar cooling. If not specified, it takes the value of the initial temperature.",
    )
    move_cooling_holes: Optional[Union[str, int, List[List[float]]]] = Field(
        default=None,
        description= "It specifies if and how cooling holes are to be moved. Either choose '1' or '2' for predefined positions or a list [[dx,dy], [dx2,dy2]].. to shift each hole manually"
    )

class MultipoleSolveHeCooling(BaseModel):
    """
    Level 4: Class for FiQuS Multipole
    """
    enabled: Optional[bool] = Field(
        default=False,
        description="It determines whether the helium cooling is enabled or not (adiabatic conditions).",
    )
    sides: Optional[Literal["external", "inner", "outer", "inner_outer"]] = Field(
        default="outer",
        description="It specifies the general grouping of the boundaries where to apply cooling:"
                    "'external': all external boundaries; 'inner': only inner boundaries; 'outer': only outer boundaries; 'inner_outer': inner and outer boundaries.",
    )
    heat_transfer_coefficient: Optional[Union[float, str]] = Field(
        default=0.0,
        description="It specifies the value or name of the function of the constant heat transfer coefficient.",
    )


class MultipoleSolveNonLinearSolver(BaseModel):
    """
    Level 4: Class for FiQuS Multipole
    """
    rel_tolerance: Optional[float] = Field(
        default=1E-4,
        description="It specifies the relative tolerance.",
    )
    abs_tolerance: Optional[float] = Field(
        default=0.1,
        description="It specifies the absolute tolerance.",
    )
    relaxation_factor: Optional[float] = Field(
        default=0.7,
        description="It specifies the relaxation factor.",
    )
    max_iterations: Optional[int] = Field(
        default=20,
        description="It specifies the maximum number of iterations if no convergence is reached.",
    )
    norm_type: Literal["L1Norm", "MeanL1Norm", "L2Norm", "MeanL2Norm", "LinfNorm"] = Field(
        default='LinfNorm',
        description="It specifies the type of norm to be calculated for convergence assessment.",
    )

class MultipoleSolveTransientThermal(MultipoleSolveTransient_parent):
    """
    Level 4: Class for FiQuS Multipole
    """
    stop_temperature: Optional[float] = Field(
        default=300,
        description="If one half turn reaches this temperature, the simulation is stopped.",
    )

class MultipoleSolveTransientCoupled(MultipoleSolveTransient_parent):
    """
    Level 4: Class for FiQuS Multipole
    """
    rel_tol_time: Optional[List[float]] = Field(
        default=[1E-4,1E-4],
        description="It specifies the relative tolerance.",
    )
    abs_tol_time: Optional[List[float]] = Field(
        default=[1e-4,1e-4],
        description="It specifies the absolute tolerance.",
    )
    norm_type: List[Literal["L1Norm", "MeanL1Norm", "L2Norm", "MeanL2Norm", "LinfNorm"]] = Field(
        default=['LinfNorm','LinfNorm'],
        description="It specifies the type of norm to be calculated for convergence assessment.",
    )
    stop_temperature: Optional[float] = Field(
        default=300,
        description="If one half turn reaches this temperature, the simulation is stopped.",
    )
    seq_NL: Optional[bool] = Field(
    default=True,
    description="The non-linear solver is sequential Mag->Thermal, or its fully coupled.",
    )

class MultipoleSolveInsulationBlockToBlock(BaseModel):
    """
    Level 4: Class for FiQuS Multipole
    It contains the information about the materials and thicknesses of the inner insulation regions (between blocks) modeled via thin-shell approximation.
    """
    material: Optional[str] = Field(
        default=None,
        description="It specifies the default material of the insulation regions between the blocks insulation regions.",
    )
    # the order of blocks should be: [inner, outer] for mid-layer couples or [lower, higher] for mid-pole and mid-winding couples
    blocks_connection_overwrite: List[Tuple[str, str]] = Field(
        default=[],
        description="It specifies the blocks couples adjacent to the insulation region."
                    "The blocks must be ordered from inner to outer block for mid-layer insulation regions and from lower to higher angle block for mid-pole and mid-winding insulation regions.",
    )
    materials_overwrite: Optional[List[List[str]]] = Field(
        default=[],
        description="It specifies the list of materials making up the layered insulation region to be placed between the specified blocks."
                    "The materials must be ordered from inner to outer layers and lower to higher angle layers.",
    )
    thicknesses_overwrite: Optional[List[List[Optional[float]]]] = Field(
        default=[],
        description="It specifies the list of thicknesses of the specified insulation layers. The order must match the one of the materials list.",
    )


class MultipoleSolveInsulationExterior(BaseModel):
    """
    Level 4: Class for FiQuS Multipole
    It contains the information about the materials and thicknesses of the outer insulation regions (exterior boundaries) modeled via thin-shell approximation.
    """
    blocks: Optional[List[str]] = Field(
        default=[],
        description="It specifies the reference numbers of the blocks adjacent to the exterior insulation regions to modify.",
    )
    materials_append: Optional[List[List[str]]] = Field(
        default=[],
        description="It specifies the list of materials making up the layered insulation region to be appended to the block insulation."
                    "The materials must be ordered from the block outward.",
    )
    thicknesses_append: Optional[List[List[float]]] = Field(
        default=[],
        description="It specifies the list of thicknesses of the specified insulation layers. The order must match the one of the materials list.",
    )

class MultipoleSolveSpecificMaterial(BaseModel):
    """
    Level 3: Class for FiQuS Multipole
    """
    material: Optional[str] = Field(
        default=None,
        description="It specifies the material of the region.",
    )
    RRR: Optional[float] = Field(
        default=None,
        description="It specifies the RRR of the region.",
    )
    T_ref_RRR_high: Optional[float] = Field(
        default=None,
        description="It specifies the reference temperature associated with the RRR.",
    )
    transient_effects_enabled: Optional[bool] = Field(
        default=False,
        description="It determines whether the transient effects are enabled or not.",
    )
    # rel_magnetic_permeability: Optional[float] = Field(
    #     default = 1.0,
    #     description = 'It specifies the material relative magnetic permeability against vacuum for EM calculations'
    # )


class MultipoleSolveInsulationCollar(BaseModel):
    material: Optional[str] = Field(
        default=None,
        description="It specifies the default material of the insulation regions between collar and outer insulation.",
    )

class MultipoleSolveInsulationTSA(BaseModel):
    """
    Level 3: Class for FiQuS Multipole
    """
    block_to_block: MultipoleSolveInsulationBlockToBlock = Field(
        default=MultipoleSolveInsulationBlockToBlock(),
        description="This dictionary contains the information about the materials and thicknesses of the inner insulation regions (between blocks) modeled via thin-shell approximation.",
    )
    exterior: Optional[MultipoleSolveInsulationExterior] = Field(
        default=MultipoleSolveInsulationExterior(),
        description="This dictionary contains the information about the materials and thicknesses of the outer insulation regions (exterior boundaries) modeled via thin-shell approximation.",
    )
    between_collar: Optional[MultipoleSolveInsulationBlockToBlock] = Field(
        default=MultipoleSolveInsulationCollar(),
        description="This dictionary contains the information about the materials and thicknesses of the insulation regions between the collar and the outer insulation regions for thin-shell approximation.",
    )

class MultipoleSolve_parent(BaseModel):
    """
    Level 3: Class for FiQuS Multipole
    """
    non_linear_solver: MultipoleSolveNonLinearSolver = Field(
        default=MultipoleSolveNonLinearSolver(),
        description="This dictionary contains the information about the parameters for the non-linear solver.",
    )


class MultipoleSolveThermal(MultipoleSolve_parent):
    """
    Level 3: Class for FiQuS Multipole
    """
    solve_type: Optional[Literal[None, "transient"]] = Field(
        default=None,
        description="It determines whether the thermal transient problem is solved ('transient') or not ('null').",
    )
    insulation_TSA: Optional[MultipoleSolveInsulationTSA] = Field(
        default=MultipoleSolveInsulationTSA(),
        description="This dictionary contains the information about the materials and thicknesses of the insulation regions modeled via thin-shell approximation.",
    )
    He_cooling: MultipoleSolveHeCooling = Field(
        default=MultipoleSolveHeCooling(),
        description="This dictionary contains the information about the Robin boundary condition for generic groups of boundaries.",
    )
    collar_cooling: MultipleSolveCollarHeCooling = Field(
        default=MultipleSolveCollarHeCooling(),
        description="This dictionary contains the information about the cooling for the collar region.",
    )
    overwrite_boundary_conditions: Optional[MultipoleSolveBoundaryConditionsThermal] = Field(
        default=MultipoleSolveBoundaryConditionsThermal(),
        description="This dictionary contains the information about boundary conditions for explicitly specified boundaries.",
    )
    time_stepping: MultipoleSolveTransientThermal = Field(
        default=MultipoleSolveTransientThermal(),
        description="This dictionary contains the information about the parameters for the transient solver.",
    )
    jc_degradation_to_zero: Optional[MultipoleSolveQuenchInitiation] = Field(
        default=MultipoleSolveQuenchInitiation(),
        description="This dictionary contains the information about half turns with zero critical current.",
    )
    init_temperature: Optional[float] = Field(
        default=1.9,
        description="It specifies the initial temperature of the simulation.",
    )
    enforce_init_temperature_as_minimum: Optional[bool] = Field(
        default=False,
        description="It determines whether the initial temperature is enforced as the minimum temperature of the simulation.",
    )

class MultipoleSolveElectromagnetics(MultipoleSolve_parent):
    """
    Level 3: Class for FiQuS Multipole
    """
    solve_type: Optional[Literal[None, "stationary","transient"]] = Field(
        default=None,
        description="It determines whether the magneto-static problem is solved ('stationary') or not ('null').",
    )
    time_stepping: Optional[MultipoleSolveTransientElectromagnetics] = Field(
        default=MultipoleSolveTransientElectromagnetics(),
        description="This dictionary contains the information about the parameters for the transient solver.",
    )


class MultipoleMeshThinShellApproximationParameters(BaseModel):
    """
    Level 4: Class for FiQuS Multipole
    """
    minimum_discretizations: Optional[int] = Field(
        default=1,
        description="It specifies the number of minimum spacial discretizations across a thin-shell.",
    )
    global_size_QH: Optional[float] = Field(
        default=1e-4,
        description="The thickness of the quench heater region is divided by this parameter to determine the number of spacial discretizations across the thin-shell.",
    )
    minimum_discretizations_QH: Optional[int] = Field(
        default=1,
        description="It specifies the number of minimum spacial discretizations across a thin-shell.",
    )
    global_size_COL: Optional[float] = Field(
        default=1e-4,
        description="The thickness of the region between ht and collar is divided by this parameter to determine the number of spacial discretizations across the thin-shell.",
    )
    minimum_discretizations_COL: Optional[int] = Field(
        default=1,
        description="It specifies the number of minimum spacial discretizations across a thin-shell.",
    )
    scale_factor_radial: Optional[float] = Field(
        default=-1.0,
        description="Scaling factor for radially directed thin-shells (e.g. halfturns to collar). Set to -1.0 to use default scaling. Wedge scalings are always ignored.",
    )
    scale_factor_azimuthal: Optional[float] = Field(
        default=-1.0,
        description="Scaling factor for azimuthally directed thin-shells (e.g. halfturns to pole). Set to -1.0 to use default scaling. Wedge scalings are always ignored.",
    )

class MultipoleMeshThreshold(BaseModel):
    """
    Level 3: Class for FiQuS Multipole
    """
    enabled: Optional[bool] = Field(
        default=False,
        description="It determines whether the gmsh Field is enabled or not.",
    )
    SizeMin: Optional[float] = Field(
        default=None,
        description="It sets gmsh Mesh.MeshSizeMin.",
    )
    SizeMax: Optional[float] = Field(
        default=None,
        description="It sets gmsh Mesh.MeshSizeMax.",
    )
    DistMin: Optional[float] = Field(
        default=None,
        description="It sets gmsh Mesh.MeshDistMin.",
    )
    DistMax: Optional[float] = Field(
        default=None,
        description="It sets gmsh Mesh.MeshDistMax.",
    )

class MultipoleMeshThresholdCollar(MultipoleMeshThreshold):
    """
    Level 3: Class for FiQuS Multipole
    """
    Enforce_TSA_mapping: Optional[bool] = Field(
        default=False,
        description="Enfocres matching nodes for the TSA layer. Uses SizeMin to determine the size of the nodes.", # only for the collar layer
    )

class MultipoleMeshTransfinite(BaseModel):
    """
    Level 3: Class for FiQuS Multipole
    """
    enabled_for: Literal[None, "curves", "curves_and_surfaces"] = Field(
        default=None,
        description="It determines on what entities the transfinite algorithm is applied.",
    )
    curve_target_size_height: Optional[float] = Field(
        default=1.0,
        description="The height of the region (short side) is divided by this parameter to determine the number of elements to apply via transfinite curves.",
    )
    curve_target_size_width: Optional[float] = Field(
        default=1.0,
        description="The width of the region (long side) is divided by this parameter to determine the number of elements to apply via transfinite curves.",
    )
class MultipoleMeshTransfiniteOrField(BaseModel):
    """
    Level 3: Class for FiQuS Multipole
    """
    transfinite: MultipoleMeshTransfinite = Field(
        default=MultipoleMeshTransfinite(),
        description="This dictionary contains the mesh information for transfinite curves.",
    )
    field: MultipoleMeshThreshold = Field(
        default=MultipoleMeshThreshold(),
        description="This dictionary contains the gmsh Field information.",
    )

class MultipolePostProc_parent(BaseModel):
    """
    Level 2: Class for FiQuS Multipole
    """
    output_time_steps_pos: Optional[Union[bool, int]] = Field(
        default=True,
        description="It determines whether the solution for the .pos file is saved for all time steps (True), none (False), or equidistant time steps (int).",
    )
    output_time_steps_txt: Optional[Union[bool, int]] = Field(
        default=True,
        description="It determines whether the solution for the .txt file is saved for all time steps (True), none (False), or equidistant time steps (int).",
    )
    save_pos_at_the_end: Optional[bool] = Field(
        default=True,
        description="It determines whether the solution for the .pos file is saved at the end of the simulation or during run time.",
    )
    save_txt_at_the_end: Optional[bool] = Field(
        default=False,
        description="It determines whether the solution for the .txt file is saved at the end of the simulation or during run time.",
    )

    plot_all: Optional[Union[bool, None]] = Field(
        default=False,
        description="It determines whether the figures are generated and shown (true), generated only (null), or not generated (false). Useful for tests.",
    )

class MultipolePostProcThermal(MultipolePostProc_parent):
    """
    Level 2: Class for FiQuS Multipole
    """
    take_average_conductor_temperature: Optional[bool] = Field(
        default=True,
        description="It determines whether the output files are based on the average conductor temperature or not (map2d).",
    )
    variables: Optional[List[Literal["T", "jOverJc", "rho", "az_thermal", "ac_loss"]]] = Field(
        default=["T"],
        description="It specifies the physical quantity to be output.",
    )
    volumes: Optional[List[
        Literal["omega", "powered", "induced", "iron", "conducting", "insulator"]]] = Field(
        default=["powered"],
        description="It specifies the regions associated with the physical quantity to be output.",
    )


class MultipolePostProcElectromagnetics(MultipolePostProc_parent):
    """
    Level 2: Class for FiQuS Multipole
    """
    compare_to_ROXIE: Optional[str] = Field(
        default=None,
        description="It contains the absolute path to a reference ROXIE map2d file. If provided, comparative plots with respect to the reference are generated.",
    )
    variables: Optional[List[Literal["a", "az", "b", "h", "js","jOverJc", "sigma_collar","is"]]] = Field(
        default=[],
        description="It specifies the physical quantity to be output.",
    )
    volumes: Optional[List[
        Literal["omega", "powered", "induced", "air", "air_far_field", "iron", "conducting", "insulator"]]] = Field(
        default=[],
        description="It specifies the regions associated with the physical quantity to be output.",
    )

class CCPostProc(BaseModel):
    variables_I: Optional[List[Literal["I_PC","I_1","I_2","I_cpc","I_crowbar","I_3","I_c_r","I_EE","I_c","I_s","I_C",
                                       "I_EE_n","I_c_n","I_s_n","I_QH","I_EQ","I_ESC",
                                       "I_A","I_B","I_C",
                                       "I_EQ",
                                       "I_ESC","I_ESC_Diode","I_ESC_C"]]] = Field(
        default=[],
        description="Currents from the circuit that will be exported as csv",
    )
    variables_U: Optional[List[Literal["PS_currentsource","PS_R_1","PS_L_1","PS_C","PS_R_3","PS_L_3","PS_R_2","PS_L_2","PS_R_crowbar","PS_Ud_crowbar","PS_L_crowbar","PS_R_c_r","PS_Ud_c_r","PS_L_c_r",
                                          "circ_R_circuit",
                                          "EE_L","EE_V_EE","EE_Ud_snubber","EE_C","EE_R_c","EE_L_c","EE_Ud_switch","EE_R_s","EE_L_s","EE_L_n","EE_V_EE_n","EE_Ud_snubber_n","EE_C_n","EE_R_c_n","EE_L_c_n","EE_Ud_switch_n","EE_R_s_n","EE_L_s_n","EE_R_switch","EE_R_switch_n",
                                          "CLIQ_R","CLIQ_L","CLIQ_C",
                                          "ECLIQ_currentsource","ECLIQ_L_leads","ECLIQ_R_leads",
                                          "ESC_C1","ESC_C2","ESC_R_leads","ESC_R_unit","ESC_L","ESC_L_Diode","ESC_Ud_Diode"]]] = Field(
        default=[],
        description="Voltages from the circuit that will be exported as csv",
    )
    assemble_veusz: Optional[bool] = Field(
        default=False,
        description="It determines whether the post-processing data is assembled in a veusz file.",
    )

class MultipolePostProc(BaseModel):
    """
    Level 2: Class for FiQuS Multipole
    """
    electromagnetics: MultipolePostProcElectromagnetics = Field(
        default=MultipolePostProcElectromagnetics(),
        description="This dictionary contains the post-processing information for the electromagnetic solution.",
    )
    thermal: MultipolePostProcThermal = Field(
        default=MultipolePostProcThermal(),
        description="This dictionary contains the post-processing information for the thermal solution.",
    )
    circuit_coupling: CCPostProc = Field(
        default= CCPostProc(),
        description="This dictionary contains the post-processing information for the circuit variables calculated in the solution.",
    )

class MultipoleSolveCoilWindingsElectricalOrder(BaseModel):
    """
    Level 2: Class for the order of the electrical pairs
    """
    group_together: Optional[List[List[int]]] = []  # elPairs_GroupTogether
    reversed: Optional[List[int]] = []  # elPairs_RevElOrder
    overwrite_electrical_order: Optional[List[int]] = []

class MultipoleSolveCoilWindings(BaseModel):
    """
        Level 1: Class for winding information
    """
    conductor_to_group: Optional[List[int]] = []  # This key assigns to each group a conductor of one of the types defined with Conductor.name
    group_to_coil_section: Optional[List[int]] = []  # This key assigns groups of half-turns to coil sections
    polarities_in_group: Optional[List[int]] = []  # This key assigns the polarity of the current in each group #
    half_turn_length: Optional[List[float]] = []
    electrical_pairs: Optional[MultipoleSolveCoilWindingsElectricalOrder] = MultipoleSolveCoilWindingsElectricalOrder()  # Variables used to calculate half-turn electrical order
    # Homogenized Multipole
class HomogenizedConductorFormulationparametersROHM(BaseModel):
    """
    Level 4: Class for finite element formulation parameters
    """
    enabled: Optional[bool] = Field(
        default=False,
        description='Use ROHM to homogenize the magnetization hysteresis in the cables.'
    )
    parameter_csv_file: Optional[str] = Field(
        default=None,
        description='Name of the csv file containing the ROHM parameters within the inputs folder with expected row structure: [alpha,kappa,chi,gamma,lambda].'
    )
    gather_cell_systems: Optional[bool] = Field(
        default = False,
        description = 'when true, it generates a single system to solve the ROHM cells instead of one system per cell to decrease generation time.'
    )
    weight_scaling: Optional[float] = Field(
        default=1.0,
        description='Downscaling factor (s<1.0) which is applied to all weights except the first, which is scaled up to compensate.'
    )
    tau_scaling: Optional[float] = Field(
        default=1.0,
        description='Scaling factor which is applied uniformly to all coupling time constants.'
    )

class HomogenizedConductorFormulationparametersROHF(BaseModel):
    """
    Level 4: Class for finite element formulation parameters
    """
    enabled: Optional[bool] = Field(
        default=False,
        description='Use ROHF to homogenize the internal flux hysteresis in the cables.'
    )
    parameter_csv_file: Optional[str] = Field(
        default=None,
        description='Name of the csv file containing the ROHF parameters within the inputs folder with expected row structure: [alpha,kappa,tau].'
    )
    gather_cell_systems: Optional[bool] = Field(
        default = False,
        description = 'when true, it generates a single system to solve the ROHF cells instead of one system per cell to decrease generation time.'
    )
class HomogenizedConductorRunType(BaseModel):
    """
    Level 4: Class for runtype parameters
    """
    mode: Optional[Literal["ramp","isothermal_ramp","quench"]] = Field(
        default="ramp",
        description= "Type of simulation to run with homogenized conductors (ramp - real cooling conditions, isothermal_ramp - unlimited cooling, quench - non-zero initial conditions)"
    )
    ramp_file: Optional[str] = Field(
        default=None,
        description='Name of the ramp model from which to start the simulation'
    )
class HomogenizedConductor(BaseModel):
    """
    Level 3: Class for FiQuS Multipole
    """
    enabled: Optional[bool] = Field(
        default=False,
        description="It determines whether the homogenized conductor model is enabled or not."
    )
    run_type: HomogenizedConductorRunType = Field(
        default=HomogenizedConductorRunType(),
        description= "Type of simulation to run with homogenized conductors (ramp - real cooling conditions, isothermal_ramp - unlimited cooling, quench - non-zero initial conditions)"
    )
    rohm: HomogenizedConductorFormulationparametersROHM = Field(
        default=HomogenizedConductorFormulationparametersROHM(),
        description="This dictionary contains the information about the parameters for the ROHM model.",
    )
    rohf: HomogenizedConductorFormulationparametersROHF = Field(
        default=HomogenizedConductorFormulationparametersROHF(),
        description="This dictionary contains the information about the parameters for the ROHF model.",
    )

class MultipoleSolve(BaseModel):
    """
    Level 2: Class for FiQuS Multipole
    """
    coil_windings: Optional[MultipoleSolveCoilWindings] = Field(
        default=MultipoleSolveCoilWindings(),
        description="This dictionary contains the information pertaining the number of coils and electrical order necessary to generate the associated electrical circuit"
        )
    electromagnetics: MultipoleSolveElectromagnetics = Field(
        default=MultipoleSolveElectromagnetics(),
        description="This dictionary contains the solver information for the electromagnetic solution.",
    )
    thermal: MultipoleSolveThermal = Field(
        default=MultipoleSolveThermal(),
        description="This dictionary contains the solver information for the thermal solution.",
    )
    wedges: MultipoleSolveSpecificMaterial = Field(
        default=MultipoleSolveSpecificMaterial(),
        description="This dictionary contains the material information of wedges.",
    )
    collar: MultipoleSolveSpecificMaterial = Field(
        default=MultipoleSolveSpecificMaterial(),
        description="This dictionary contains the material information of the collar region.",
    )
    iron_yoke: MultipoleSolveSpecificMaterial = Field(
        default=MultipoleSolveSpecificMaterial(),
        description="This dictionary contains the material information of the iron yoke region.",
    )
    poles: MultipoleSolveSpecificMaterial = Field(
        default=MultipoleSolveSpecificMaterial(),
        description="This dictionary contains the material information of the pole region.",
    )
    noOfMPITasks: Optional[Union[bool, int]] = Field(
        default=False,
        title="No. of tasks for MPI parallel run of GetDP",
        description=(
            "If integer, GetDP will be run in parallel using MPI. This is only valid"
            " if MPI is installed on the system and an MPI-enabled GetDP is used." 
            " If False, GetDP will be run in serial without invoking mpiexec."
        ),
    )
    time_stepping: Optional[MultipoleSolveTransientCoupled] = Field(
        default=MultipoleSolveTransientCoupled(),
        description="This dictionary contains the information about the parameters for the transient solver.",
    )
    cable_homogenization: Optional[HomogenizedConductor]= Field(
        default=HomogenizedConductor(),
        description="This dictionary contains the information about the homogenized conductor properties.",
    )

class MultipoleThermalInsulationMesh(BaseModel):
    """
    Level 3: Class for FiQuS Multipole
    """
    global_size: float = Field(
        default=1e-4,
        description="It specifies the global size of the mesh for the insulation regions. It is enforced as a constant mesh field for surface insulation and by fixing the number of TSA layers for thin-shell approximation.",
    )
    TSA: Optional[MultipoleMeshThinShellApproximationParameters] = Field(
        default=MultipoleMeshThinShellApproximationParameters(),
        description="This dictionary contains the mesh information for thin-shells.",
    )

class MultipoleMesh_parent(BaseModel):
    """
    Level 2: Class for FiQuS Multipole
    """
    create: bool = Field(
        default=True,
        description="It determines whether the mesh is built or not.",
    )
    conductors: Optional[MultipoleMeshTransfiniteOrField] = Field(
        default=MultipoleMeshTransfiniteOrField(),
        description="This dictionary contains the mesh information for the conductor regions.",
    )
    wedges: Optional[MultipoleMeshTransfiniteOrField] = Field(
        default=MultipoleMeshTransfiniteOrField(),
        description="This dictionary contains the mesh information for the wedge regions.",
    )
    iron_field: Optional[MultipoleMeshThreshold] = Field(
        default=MultipoleMeshThreshold(),
        description="This dictionary contains the gmsh Field information for the iron yoke region.",
    )
    collar: Optional[MultipoleMeshThresholdCollar] = Field(
        default=MultipoleMeshThresholdCollar(),
        description="This dictionary contains the gmsh Field information for the collar region.",
    )
    poles: Optional[MultipoleMeshThreshold] = Field(
        default=MultipoleMeshThreshold(),
        description="This dictionary contains the mesh information for the poles region.",
    )

class MultipoleMeshThermal(MultipoleMesh_parent):
    """
    Level 2: Class for FiQuS Multipole
    """
    reference: Optional[MultipoleMeshThreshold] = Field(
        default=MultipoleMeshThreshold(),
        description="It determines whether the reference mesh is built or not. If True, an additional layer between the insulation and collar is meshed",
    )
    insulation: Optional[MultipoleThermalInsulationMesh] = Field(
        default=MultipoleThermalInsulationMesh(),
        description="This dictionary contains the mesh information for the insulation regions.",
    )
    isothermal_conductors: Optional[bool] = Field(
        default=False,
        description="It determines whether the conductors are considered isothermal or not using getDP constraints.",
    )
    isothermal_wedges: Optional[bool] = Field(
        default=False,
        description="It determines whether the wedges are considered isothermal or not using getDP Link constraints.",
    )

class MultipoleMeshElectromagnetics(MultipoleMesh_parent):
    """
    Level 2: Class for FiQuS Multipole
    """
    bore_field: Optional[MultipoleMeshThreshold] = Field(
        default=MultipoleMeshThreshold(),
        description="This dictionary contains the gmsh Field information for the bore region.",
    )

class MultipoleMesh(BaseModel):
    """
    Level 2: Class for FiQuS Multipole
    """
    electromagnetics: MultipoleMeshElectromagnetics = Field(
        default=MultipoleMeshElectromagnetics(),
        description="This dictionary contains the mesh information for the electromagnetic solution.",
    )
    thermal: MultipoleMeshThermal = Field(
        default=MultipoleMeshThermal(),
        description="This dictionary contains the mesh information for the thermal solution.",
    )

class MultipoleGeometry_parent(BaseModel):
    create: bool = Field(
        default=True,
        description="It determines whether the geometry is built or not.",
    )
    with_wedges: Optional[bool] = Field(
        default=True,
        description="It determines whether the wedge regions are built or not.",
    )
    areas: Optional[List[Literal["iron_yoke", "collar", "poles"]]] = Field(
        default= [],
        description="List with areas to build."
    )

class MultipoleGeometryThermal(MultipoleGeometry_parent):
    """
    Level 2: Class for FiQuS Multipole
    """
    use_TSA: Optional[bool] = Field(
        default=False,
        description="It determines whether the insulation regions are explicitly built or modeled via thin-shell approximation.",
    )
    correct_block_coil_tsa_checkered_scheme: Optional[bool] = Field(
        default=False,
        description="There is a bug in the TSA naming scheme for block coils, this flag activates a simple (not clean) bug fix that will be replaced in a future version.",
    )
    use_TSA_new: Optional[bool] = Field(
        default=False,
        description="It determines whether the regions between collar and coils are modeled via thin-shell approximation.",
    )

class MultipoleGeometryElectromagnetics(MultipoleGeometry_parent):
    """
    Level 2: Class for FiQuS Multipole
    """
    symmetry: Optional[Literal["none", "xy", "x", "y"]] = Field(
        default='none',
        description="It determines the model regions to build according to the specified axis/axes.",
    )

class MultipoleGeometry(BaseModel):
    """
    Level 2: Class for FiQuS Multipole
    """
    geom_file_path: Optional[str] = Field(
        default=None,
        description="It contains the path to a .geom file. If null, the default .geom file produced by steam-sdk BuilderFiQuS will be used.",
    )
    plot_preview: Optional[bool] = Field(
        default=False,
        description="If true, it displays matplotlib figures of the magnet geometry with relevant information (e.g., conductor and block numbers).",
    )
    electromagnetics: MultipoleGeometryElectromagnetics = Field(
        default=MultipoleGeometryElectromagnetics(),
        description="This dictionary contains the geometry information for the electromagnetic solution.",
    )
    thermal: MultipoleGeometryThermal = Field(
        default=MultipoleGeometryThermal(),
        description="This dictionary contains the geometry information for the thermal solution.",
    )


class Multipole(BaseModel):
    """
    Level 1: Class for FiQuS Multipole
    """
    type: Literal["multipole"] = "multipole"
    geometry: MultipoleGeometry = Field(
        default=MultipoleGeometry(),
        description="This dictionary contains the geometry information.",
    )
    mesh: MultipoleMesh = Field(
        default=MultipoleMesh(),
        description="This dictionary contains the mesh information.",
    )
    solve: MultipoleSolve = Field(
        default=MultipoleSolve(),
        description="This dictionary contains the solution information.",
    )
    postproc: MultipolePostProc = Field(
        default=MultipolePostProc(),
        description="This dictionary contains the post-process information.",
    )