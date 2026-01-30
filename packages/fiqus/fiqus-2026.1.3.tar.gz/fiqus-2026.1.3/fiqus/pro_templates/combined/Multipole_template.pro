{% set USE_THERMAL_PROJECTION = False %}
{#
    DefineConstant[
C_ = {"-solve -v2 -pos -mat_mumps_icntl_14 100", Name "Updated_CvFUN/9ComputeCommand"}];// C_ = {"-solve -v2 -pos -pc_type lu -pc_factor_mat_solver_type umfpack", Name "GetDP/9ComputeCommand"}];
#}
{# // DEFINITION OF THE OPERATION MODE #}
{# // - Magnetostatics: Mag_sta  #}
{# // - Magnetodynamics (Zero initial condition): Mag_dyn_0  #}
{# // - Magnetodynamics: Mag_dyn  #}
{# // - Thermal-Magnetostatics: Th_Mag_sta  #}
{# // - Thermal-Magnetodynamics (Zero initial condition): Th_Mag_0  #}
{# // - Thermal-Magnetodynamics: Th_Mag  #}
{% if dm.magnet.solve.electromagnetics.solve_type == 'stationary' %}
    {% if dm.magnet.solve.thermal.solve_type %}
        {% set SIM_MODE =  'Th_Mag_sta'%}
    {% else %}
        {% set SIM_MODE =  'Mag_sta'%}
    {% endif %}
{% elif dm.magnet.solve.thermal.solve_type %}
    {% if dm.power_supply.I_control_LUT[0] != 0 %}
        {% set SIM_MODE =  'Th_Mag'%}
    {% else %}
        {% set SIM_MODE =  'Th_Mag_0'%}
    {% endif %}
{% else %}
    {% if  dm.power_supply.I_control_LUT[0] != 0%}
    {% set SIM_MODE =  'Mag_dyn'%}
    {% else %}
        {% set SIM_MODE =  'Mag_dyn_0'%}
    {% endif %}
{% endif %}

{#//Critical Current depending on the material of the superconductor #}
{%- macro criticalCurrentDensity(region_name, cond, time_trigger, cond_name) %}
    {%- if cond.Jc_fit.type == 'CUDI1' %}
    {%- if cond.strand.type == 'Round' %}
        {%- set wire_diameter = (cond.cable.n_strands)**(1/2) * cond.strand.diameter %}
    {%- elif cond.strand.type == 'Rectangular' %}
        {%- set n_strands = cond.cable.n_strands if cond.cable.type == 'Rutherford' else 1 %}
        {%- set wire_diameter = (4 * n_strands * cond.strand.bare_width * cond.strand.bare_height / Pi) ** (1 / 2) %}
    {%- endif -%}
    criticalCurrentDensity[<<region_name>>] = $Time > <<time_trigger>>? 0: <<materials[criticalCurrentDensityMacroName[cond.strand.material_superconductor + '_' + cond.Jc_fit.type]](C1=cond.Jc_fit.C1_CUDI1, C2=cond.Jc_fit.C2_CUDI1, Tc0=cond.Jc_fit.Tc0_CUDI1, Bc20=cond.Jc_fit.Bc20_CUDI1, wireDiameter=wire_diameter, Cu_noCu=cond.strand.Cu_noCu_in_strand)>> * f_sc_<<cond_name>>;
    {%- elif cond.Jc_fit.type == 'Summers' -%}
    criticalCurrentDensity[<<region_name>>] = $Time > <<time_trigger>>? 0: <<materials[criticalCurrentDensityMacroName[cond.strand.material_superconductor + '_' + cond.Jc_fit.type]](Jc0=cond.Jc_fit.Jc0_Summers, Tc0=cond.Jc_fit.Tc0_Summers, Bc20=cond.Jc_fit.Bc20_Summers)>> * f_sc_<<cond_name>>;
    {%- elif cond.Jc_fit.type == 'Bordini' %}
    criticalCurrentDensity[<<region_name>>] = $Time > <<time_trigger>>? 0: <<materials[criticalCurrentDensityMacroName[cond.strand.material_superconductor + '_' + cond.Jc_fit.type]](Tc0=cond.Jc_fit.Tc0_Bordini, Bc20=cond.Jc_fit.Bc20_Bordini, C0=cond.Jc_fit.C0_Bordini, alpha=cond.Jc_fit.alpha_Bordini)>> * f_sc_<<cond_name>>;
    {%- elif cond.Jc_fit.type == 'BSCCO_2212_LBNL' %}
    criticalCurrentDensity[<<region_name>>] = $Time > <<time_trigger>>? 0: <<materials[criticalCurrentDensityMacroName[cond.strand.material_superconductor + '_' + cond.Jc_fit.type]](f_scaling=cond.Jc_fit.f_scaling_Jc_BSCCO2212)>>  * f_sc_<<cond_name>>;
    {%- endif -%}
{% endmacro %}

Include "<<BHcurves>>";?
{% import "materials.pro" as materials %}
{% import "TSA_materials.pro" as TSA_materials %}
{% import "CC_Module.pro" as cc_macros2 -%}
{% set areas_to_build = {'EM': dm.magnet.geometry.electromagnetics.areas, 'TH': dm.magnet.geometry.thermal.areas } %}
{% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Th_Mag_sta' %}
    // Preamble
    // Stop the simulation when the Avg. temperature of any of the half-turns reaches the stop temp.
    {%  if dm.magnet.solve.thermal.solve_type and dm.magnet.solve.electromagnetics.solve_type == 'transient'%}
    stop_temperature = <<dm.magnet.solve.time_stepping.stop_temperature>>; // [K]
    {%  else %}
    stop_temperature = <<dm.magnet.solve.thermal.time_stepping.stop_temperature>>; // [K]
    {%  endif %}
    /* -------------------------------------------------------------------------- */
    {% if dm.magnet.geometry.thermal.use_TSA %}
        {#
        // Checkered support indexing for bare part
        // first index: neighboring information in azimuthal direction
        // second index: neighboring information in radial direction
        #}
        {% if dm.magnet.geometry.thermal.with_wedges %}
         {% set bare_1_1 = rm_TH.powered['r1_a1'].vol.numbers + rm_TH.induced['r1_a1'].vol.numbers %}
         {% set bare_2_1 = rm_TH.powered['r2_a1'].vol.numbers + rm_TH.induced['r2_a1'].vol.numbers %}
         {% set bare_1_2 = rm_TH.powered['r1_a2'].vol.numbers + rm_TH.induced['r1_a2'].vol.numbers %}
         {% set bare_2_2 = rm_TH.powered['r2_a2'].vol.numbers + rm_TH.induced['r2_a2'].vol.numbers %}
        {% else %}
         {% set bare_1_1 = rm_TH.powered['r1_a1'].vol.numbers %}
         {% set bare_2_1 = rm_TH.powered['r2_a1'].vol.numbers %}
         {% set bare_1_2 = rm_TH.powered['r1_a2'].vol.numbers %}
         {% set bare_2_2 = rm_TH.powered['r2_a2'].vol.numbers %}
        {% endif %}

        bare_1_1 = {<<bare_1_1|join(', ')>>};
        bare_2_1 = {<<bare_2_1|join(', ')>>};
        bare_1_2 = {<<bare_1_2|join(', ')>>};
        bare_2_2 = {<<bare_2_2|join(', ')>>};

        // Shell lines belonging to the bare parts as indexed above
        {% if dm.magnet.geometry.thermal.with_wedges %}
         {% set bare_layers_1_1 = rm_TH.powered['r1_a1'].surf_in.numbers  +  rm_TH.induced['r1_a1'].surf_in.numbers %}
         {% set bare_layers_2_1 = rm_TH.powered['r2_a1'].surf_in.numbers  +  rm_TH.induced['r2_a1'].surf_in.numbers %}
         {% set bare_layers_1_2 = rm_TH.powered['r1_a2'].surf_in.numbers  +  rm_TH.induced['r1_a2'].surf_in.numbers %}
         {% set bare_layers_2_2 = rm_TH.powered['r2_a2'].surf_in.numbers  +  rm_TH.induced['r2_a2'].surf_in.numbers %}
        {% else %}
         {% set bare_layers_1_1 = rm_TH.powered['r1_a1'].surf_in.numbers %}
         {% set bare_layers_2_1 = rm_TH.powered['r2_a1'].surf_in.numbers %}
         {% set bare_layers_1_2 = rm_TH.powered['r1_a2'].surf_in.numbers %}
         {% set bare_layers_2_2 = rm_TH.powered['r2_a2'].surf_in.numbers %}
        {% endif %}

        bare_layers_1_1() = {<<bare_layers_1_1|join(', ')>>};
        bare_layers_2_1() = {<<bare_layers_2_1|join(', ')>>};
        bare_layers_1_2() = {<<bare_layers_1_2|join(', ')>>};
        bare_layers_2_2() = {<<bare_layers_2_2|join(', ')>>};

        // ------------ BOUNDARY CONDITIONS --------------------------------------------
        {#
        // boundary shells where Dirichlet BC applied, there we need two Tdisc
        // indexing follows the one with the bares BUT we have to think of these lines
        // as neighbors belonging to the non-existing exterior bare part, i.e.,
        // the line touching bare_2_1 will then be bare_1_1
        #}
        bndDir_1_1() = {<<rm_TH.boundaries.thermal.temperature.groups['r1_a1']|join(', ')>>};
        bndDir_2_1() = {<<rm_TH.boundaries.thermal.temperature.groups['r2_a1']|join(', ')>>};
        bndDir_1_2() = {<<rm_TH.boundaries.thermal.temperature.groups['r1_a2']|join(', ')>>};
        bndDir_2_2() = {<<rm_TH.boundaries.thermal.temperature.groups['r2_a2']|join(', ')>>};
        {#
        // boundary shells where Neumann BC applied, there we need two Tdisc
        // indexing follows the one with the bares BUT we have to think of these lines
        // as neighbors belonging to the non-existing exterior bare part, i.e.,
        // the line touching bare_2_1 will then be bare_1_1
        #}
        bndNeu_1_1() = {<<rm_TH.boundaries.thermal.heat_flux.groups['r1_a1']|join(', ')>>};
        bndNeu_2_1() = {<<rm_TH.boundaries.thermal.heat_flux.groups['r2_a1']|join(', ')>>};
        bndNeu_1_2() = {<<rm_TH.boundaries.thermal.heat_flux.groups['r1_a2']|join(', ')>>};
        bndNeu_2_2() = {<<rm_TH.boundaries.thermal.heat_flux.groups['r2_a2']|join(', ')>>};
        {#
        // boundary shells where Robin BC applied, follows the same indexing scheme as
        // Dirichlet, i.e.,
        // indexing follows the one with the bares BUT we have to think of these lines
        // as neighbors belonging to the non-existing exterior bare part, i.e.,
        // the line touching bare_2_1 will then be bare_1_1
        #}
        bndRobin_1_1() = { <<rm_TH.boundaries.thermal.cooling.groups['r1_a1']|join(', ')>>};
        bndRobin_2_1() = { <<rm_TH.boundaries.thermal.cooling.groups['r2_a1']|join(', ')>>};
        bndRobin_1_2() = { <<rm_TH.boundaries.thermal.cooling.groups['r1_a2']|join(', ')>>};
        bndRobin_2_2() = { <<rm_TH.boundaries.thermal.cooling.groups['r2_a2']|join(', ')>>};
        {#
        // for Robin and Neumann, we also need to store some information for GetDP to know the
        // outer virtual shell element
        // first index: same as first index of horVer_layers of Robin (simplified) or midLayers (non-simplified)
        // second index: same as first index of bndRobin or bndNeumann
        // third index: same as second index of bndRobin or bndNeumann
        #}
        {% set bndRobinInt_1_1_1 =  list(set(rm_TH.boundaries.thermal.cooling.groups['r1_a1']).intersection(bare_layers_2_1)) %}
        {% set bndRobinInt_2_1_1 =  list(set(rm_TH.boundaries.thermal.cooling.groups['r1_a1']).intersection(bare_layers_1_2)) %}
        {% set bndRobinInt_1_2_1 =  list(set(rm_TH.boundaries.thermal.cooling.groups['r2_a1']).intersection(bare_layers_1_1)) %}
        {% set bndRobinInt_2_2_1 =  list(set(rm_TH.boundaries.thermal.cooling.groups['r2_a1']).intersection(bare_layers_2_2)) %}
        {% set bndRobinInt_1_1_2 =  list(set(rm_TH.boundaries.thermal.cooling.groups['r1_a2']).intersection(bare_layers_2_2)) %}
        {% set bndRobinInt_2_1_2 =  list(set(rm_TH.boundaries.thermal.cooling.groups['r1_a2']).intersection(bare_layers_1_1)) %}
        {% set bndRobinInt_1_2_2 =  list(set(rm_TH.boundaries.thermal.cooling.groups['r2_a2']).intersection(bare_layers_1_2)) %}
        {% set bndRobinInt_2_2_2 =  list(set(rm_TH.boundaries.thermal.cooling.groups['r2_a2']).intersection(bare_layers_2_1)) %}

        // Neumann
        {% set bndNeuInt_1_1_1 =  list(set(rm_TH.boundaries.thermal.heat_flux.groups['r1_a1']).intersection(bare_layers_2_1)) %}
        {% set bndNeuInt_2_1_1 =  list(set(rm_TH.boundaries.thermal.heat_flux.groups['r1_a1']).intersection(bare_layers_1_2)) %}
        {% set bndNeuInt_1_2_1 =  list(set(rm_TH.boundaries.thermal.heat_flux.groups['r2_a1']).intersection(bare_layers_1_1)) %}
        {% set bndNeuInt_2_2_1 =  list(set(rm_TH.boundaries.thermal.heat_flux.groups['r2_a1']).intersection(bare_layers_2_2)) %}
        {% set bndNeuInt_1_1_2 =  list(set(rm_TH.boundaries.thermal.heat_flux.groups['r1_a2']).intersection(bare_layers_2_2)) %}
        {% set bndNeuInt_2_1_2 =  list(set(rm_TH.boundaries.thermal.heat_flux.groups['r1_a2']).intersection(bare_layers_1_1)) %}
        {% set bndNeuInt_1_2_2 =  list(set(rm_TH.boundaries.thermal.heat_flux.groups['r2_a2']).intersection(bare_layers_1_2)) %}
        {% set bndNeuInt_2_2_2 =  list(set(rm_TH.boundaries.thermal.heat_flux.groups['r2_a2']).intersection(bare_layers_2_1)) %}

        // QH
        {% set ns = namespace(all_QH=[]) %}
        {% for taglist in rm_TH.thin_shells.quench_heaters.thin_shells %}
            {% set ns.all_QH = ns.all_QH + taglist %}
        {% endfor %}
        {% set QH_1_1 = set(ns.all_QH).intersection(set(bare_layers_2_1).intersection(rm_TH.thin_shells.normals_directed['azimuthally']).union(set(bare_layers_1_2).intersection(rm_TH.thin_shells.normals_directed['radially'])))  %}
        {% set QH_2_1 = set(ns.all_QH).intersection(set(bare_layers_1_1).intersection(rm_TH.thin_shells.normals_directed['azimuthally']).union(set(bare_layers_2_2).intersection(rm_TH.thin_shells.normals_directed['radially'])))  %}
        {% set QH_1_2 = set(ns.all_QH).intersection(set(bare_layers_2_2).intersection(rm_TH.thin_shells.normals_directed['azimuthally']).union(set(bare_layers_1_1).intersection(rm_TH.thin_shells.normals_directed['radially'])))  %}
        {% set QH_2_2 = set(ns.all_QH).intersection(set(bare_layers_1_2).intersection(rm_TH.thin_shells.normals_directed['azimuthally']).union(set(bare_layers_2_1).intersection(rm_TH.thin_shells.normals_directed['radially'])))  %}
        QH_1_1() = {<<QH_1_1|join(', ')>>};
        QH_2_1() = {<<QH_2_1|join(', ')>>};
        QH_1_2() = {<<QH_1_2|join(', ')>>};
        QH_2_2() = {<<QH_2_2|join(', ')>>};
        // midLayers
        {% if dm.magnet.geometry.thermal.with_wedges %}
         {% set midLayers_1_1 = rm_TH.powered['r1_a1'].surf_out.numbers  +  rm_TH.induced['r1_a1'].surf_out.numbers %}
         {% set midLayers_2_1 = rm_TH.powered['r2_a1'].surf_out.numbers  +  rm_TH.induced['r2_a1'].surf_out.numbers %}
         {% set midLayers_1_2 = rm_TH.powered['r1_a2'].surf_out.numbers  +  rm_TH.induced['r1_a2'].surf_out.numbers %}
        {% set midLayers_2_2 = rm_TH.powered['r2_a2'].surf_out.numbers  +  rm_TH.induced['r2_a2'].surf_out.numbers %}
        {% else %}
         {% set midLayers_1_1 = rm_TH.powered['r1_a1'].surf_out.numbers %}
         {% set midLayers_2_1 = rm_TH.powered['r2_a1'].surf_out.numbers %}
         {% set midLayers_1_2 = rm_TH.powered['r1_a2'].surf_out.numbers %}
         {% set midLayers_2_2 = rm_TH.powered['r2_a2'].surf_out.numbers %}
        {% endif %}
        midLayers_1_1() = {<<midLayers_1_1|join(', ')>>};
        midLayers_2_1() = {<<midLayers_2_1|join(', ')>>};
        midLayers_1_2() = {<<midLayers_1_2|join(', ')>>};
        midLayers_2_2() = {<<midLayers_2_2|join(', ')>>};
        midLayers() = {<<rm_TH.thin_shells.mid_turns_layers_poles|join(', ')>>};

        {# midLayers_1: oriented along radial direction, connecting half-turns and poles #}
        {# part of the vertical and horizontal splitting #}
        {# it needs to match the definition of the function spaces for identifying plus and minus side correctly #}
        {% set midLayers_1 = list(set(rm_TH.thin_shells.normals_directed['azimuthally']).intersection(rm_TH.thin_shells.mid_turns_layers_poles)) %}
        {# midLayers_2: oriented along azimuth direction, connecting layer # }
        {# part of the vertical and horizontal splitting #}
        {% set midLayers_2 = list(set(rm_TH.thin_shells.normals_directed['radially']).intersection(rm_TH.thin_shells.mid_turns_layers_poles)) %}
        {% if dm.magnet.geometry.thermal.use_TSA_new %}
         inner_collar = {<<rm_TH.thin_shells.bdry_curves.collar|join(',')>>};
         pole_bdry_lines = {<<rm_TH.thin_shells.bdry_curves.poles|join(',')>>};
        {% endif %}
    {% endif %}
    outer_collar = {<<rm_TH.thin_shells.bdry_curves.outer_collar|join(',')>>};
            {% if dm.magnet.geometry.thermal.with_wedges %}
    indLayers={{% if rm_TH.induced['r1_a1'].surf_in.numbers %} <<rm_TH.induced['r1_a1'].surf_in.numbers|join(', ')>>{% endif %}
                 {% if rm_TH.induced['r2_a1'].surf_in.numbers %}, <<rm_TH.induced['r2_a1'].surf_in.numbers|join(', ')>>{% endif %}
                 {% if rm_TH.induced['r1_a2'].surf_in.numbers %}, <<rm_TH.induced['r1_a2'].surf_in.numbers|join(', ')>>{% endif %}
                 {% if rm_TH.induced['r2_a2'].surf_in.numbers %}, <<rm_TH.induced['r2_a2'].surf_in.numbers|join(', ')>>{% endif %}
                 };
        {% endif %}
    // AUX GROUPS ------------------------------------------------------------------
    allLayers = {{% if rm_TH.powered['r1_a1'].surf_in.numbers %}<<rm_TH.powered['r1_a1'].surf_in.numbers|join(', ')>>{% endif %}
                 {% if rm_TH.powered['r2_a1'].surf_in.numbers %}, <<rm_TH.powered['r2_a1'].surf_in.numbers|join(', ')>>{% endif %}
                 {% if rm_TH.powered['r1_a2'].surf_in.numbers %}, <<rm_TH.powered['r1_a2'].surf_in.numbers|join(', ')>>{% endif %}
                 {% if rm_TH.powered['r2_a2'].surf_in.numbers %}, <<rm_TH.powered['r2_a2'].surf_in.numbers|join(', ')>>{% endif %}
                 {% if dm.magnet.geometry.thermal.with_wedges %}
                 {% if rm_TH.induced['r1_a1'].surf_in.numbers %}, <<rm_TH.induced['r1_a1'].surf_in.numbers|join(', ')>>{% endif %}
                 {% if rm_TH.induced['r2_a1'].surf_in.numbers %}, <<rm_TH.induced['r2_a1'].surf_in.numbers|join(', ')>>{% endif %}
                 {% if rm_TH.induced['r1_a2'].surf_in.numbers %}, <<rm_TH.induced['r1_a2'].surf_in.numbers|join(', ')>>{% endif %}
                 {% if rm_TH.induced['r2_a2'].surf_in.numbers %}, <<rm_TH.induced['r2_a2'].surf_in.numbers|join(', ')>>{% endif %}
                 {% endif %}};
{% endif %}

Group {
    // Extra groups: cooling of the collar
    bndCollarGaps = Region[{ {% if dm.magnet.solve.thermal.collar_cooling.enabled %}<<rm_TH.boundaries.thermal.collar.bc.numbers|join(',')>> {% endif %}}];

    // Air Volume Regions
    <<rm_EM.air.vol.name>> = Region[ <<rm_EM.air.vol.number>> ];  // Air
    <<rm_EM.air_far_field.vol.names[0]>> = Region[ <<rm_EM.air_far_field.vol.numbers[0]>> ];  // AirInf
    // Half-turn Volume Regions
    {% for name, number in zip(rm_EM.powered['r1_a1'].vol.names, rm_EM.powered['r1_a1'].vol.numbers) %}
    <<name>> = Region[ <<number>> ];
    {% endfor %}
    {% for name, number in zip(rm_EM.powered['r2_a1'].vol.names, rm_EM.powered['r2_a1'].vol.numbers) %}
    <<name>> = Region[ <<number>> ];
    {% endfor %}
    {% for name, number in zip(rm_EM.powered['r1_a2'].vol.names, rm_EM.powered['r1_a2'].vol.numbers) %}
    <<name>> = Region[ <<number>> ];
    {% endfor %}
    {% for name, number in zip(rm_EM.powered['r2_a2'].vol.names, rm_EM.powered['r2_a2'].vol.numbers) %}
    <<name>> = Region[ <<number>> ];
    {% endfor %}

    {% if dm.magnet.solve.thermal.solve_type %}
    // Half-turn Volume Regions for Thermal
        {% for name, number in zip(rm_TH.powered['r1_a1'].vol.names, rm_TH.powered['r1_a1'].vol.numbers) %}
    <<name>> = Region[ <<number>> ];
        {% endfor %}
        {% for name, number in zip(rm_TH.powered['r2_a1'].vol.names, rm_TH.powered['r2_a1'].vol.numbers) %}
    <<name>> = Region[ <<number>> ];
        {% endfor %}
        {% for name, number in zip(rm_TH.powered['r1_a2'].vol.names, rm_TH.powered['r1_a2'].vol.numbers) %}
    <<name>> = Region[ <<number>> ];
        {% endfor %}
        {% for name, number in zip(rm_TH.powered['r2_a2'].vol.names, rm_TH.powered['r2_a2'].vol.numbers) %}
    <<name>> = Region[ <<number>> ];
        {% endfor %}
    {% endif -%}

    {% if dm.magnet.geometry.electromagnetics.with_wedges %}
    //Wedges Volume Regions for EM
      {% for name, number in zip(rm_EM.induced['r1_a1'].vol.names, rm_EM.induced['r1_a1'].vol.numbers) %}
    <<name>> = Region[ <<number>> ];
      {% endfor %}
      {% for name, number in zip(rm_EM.induced['r2_a1'].vol.names, rm_EM.induced['r2_a1'].vol.numbers) %}
    <<name>> = Region[ <<number>> ];
      {% endfor %}
      {% for name, number in zip(rm_EM.induced['r1_a2'].vol.names, rm_EM.induced['r1_a2'].vol.numbers) %}
    <<name>> = Region[ <<number>> ];
      {% endfor %}
      {% for name, number in zip(rm_EM.induced['r2_a2'].vol.names, rm_EM.induced['r2_a2'].vol.numbers) %}
    <<name>> = Region[ <<number>> ];
      {% endfor %}
    {% endif -%}


    {% if dm.magnet.solve.thermal.solve_type %}
        {% if dm.magnet.geometry.thermal.with_wedges %}
    //Wedges Volume Regions for EM
            {% for name, number in zip(rm_TH.induced['r1_a1'].vol.names, rm_TH.induced['r1_a1'].vol.numbers) %}
    <<name>> = Region[ <<number>> ];
            {% endfor %}
            {% for name, number in zip(rm_TH.induced['r2_a1'].vol.names, rm_TH.induced['r2_a1'].vol.numbers) %}
    <<name>> = Region[ <<number>> ];
            {% endfor %}
            {% for name, number in zip(rm_TH.induced['r1_a2'].vol.names, rm_TH.induced['r1_a2'].vol.numbers) %}
    <<name>> = Region[ <<number>> ];
            {% endfor %}
            {% for name, number in zip(rm_TH.induced['r2_a2'].vol.names, rm_TH.induced['r2_a2'].vol.numbers) %}
    <<name>> = Region[ <<number>> ];
            {% endfor %}
        {% endif %}
    {% endif -%}    
    //Iron Volumes Region for EM
    {% for area in areas_to_build['EM'] %}
        {% for name, number in zip(rm_EM[area].vol.names, rm_EM[area].vol.numbers) %}
    S<<nc[area]>>_<<name>> = Region[ <<number>> ];
        {% endfor %}
    {% endfor %}

    {% if dm.magnet.solve.thermal.solve_type %}
    //Iron Volumes Region for Thermal
        {% for region in areas_to_build['TH'] %}
            {% for name, number in zip(rm_TH[region].vol.names, rm_TH[region].vol.numbers) %}
    S<<nc[region]>>_<<name>>_TH = Region[ <<number>> ];
            {% endfor %}
        {% endfor %}
        {% if dm.magnet.mesh.thermal.reference.enabled %}
    // reference solution
            {% for name, number in zip(rm_TH['ref_mesh'].vol.names, rm_TH['ref_mesh'].vol.numbers) %}
    S<<nc['ref_mesh']>>_<<name>>_TH = Region[ <<number>> ];
            {% endfor %}
        {% endif %}
    {% endif %}

    // Air Far Field Surface Region
    <<rm_EM.air_far_field.surf.name>> = Region[ <<rm_EM.air_far_field.surf.number>> ];
    {% if rm_EM.boundaries.symmetry.normal_free.number %}
    <<rm_EM.boundaries.symmetry.normal_free.name>> = Region[ <<rm_EM.boundaries.symmetry.normal_free.number>> ];
    {% endif -%}

    {% if dm.magnet.solve.thermal.solve_type %}
        {% if not dm.magnet.geometry.thermal.use_TSA %}
    // Insulator Volume Regions for TSA
            {% for name, number in zip(rm_TH.insulator.vol.names, rm_TH.insulator.vol.numbers) %}
    <<name>> = Region[ <<number>> ];
            {% endfor %}
            {% for name, number in zip(rm_TH.insulator.surf.names, rm_TH.insulator.surf.numbers) %}
    <<name>> = Region[ <<number>> ];
            {% endfor %}
        {% endif %}
    {% endif %}

    //Groups
    <<nc.omega>><<nc.air>>_EM = Region[ <<rm_EM.air.vol.name>> ];
    <<nc.omega>><<nc.air_far_field>>_EM = Region[ <<rm_EM.air_far_field.vol.names[0]>> ];
    // Half-Turn Conductors Groups for EM
    {% for cond_name in dm.conductors.keys() %}
    <<nc.omega>><<nc.powered>>_<<cond_name>>_EM = Region[ {
                {%- if rm_EM.powered['r1_a1'].conductors[cond_name] %} <<rm_EM.powered['r1_a1'].conductors[cond_name]|join(', ')>>{% endif %}
                {% if rm_EM.powered['r1_a2'].conductors[cond_name] %}, <<rm_EM.powered['r1_a2'].conductors[cond_name]|join(', ')>>{% endif %}
                {% if rm_EM.powered['r2_a1'].conductors[cond_name] %}, <<rm_EM.powered['r2_a1'].conductors[cond_name]|join(', ')>>{% endif %}
                {% if rm_EM.powered['r2_a2'].conductors[cond_name] %}, <<rm_EM.powered['r2_a2'].conductors[cond_name]|join(', ')>>{% endif %}} ];
        {% if dm.magnet.solve.thermal.solve_type %}
    <<nc.omega>><<nc.powered>>_<<cond_name>>_TH = Region[ {
                {%- if rm_TH.powered['r1_a1'].conductors[cond_name] %}<<rm_TH.powered['r1_a1'].conductors[cond_name]|join(', ')>>{% endif %}
                {% if rm_TH.powered['r1_a2'].conductors[cond_name] %}, <<rm_TH.powered['r1_a2'].conductors[cond_name]|join(', ')>>{% endif %}
                {% if rm_TH.powered['r2_a1'].conductors[cond_name] %}, <<rm_TH.powered['r2_a1'].conductors[cond_name]|join(', ')>>{% endif %}
                {% if rm_TH.powered['r2_a2'].conductors[cond_name] %}, <<rm_TH.powered['r2_a2'].conductors[cond_name]|join(', ')>>{% endif %}} ];
        {% endif %}
    {% endfor %}
    //Powered Group
    <<nc.omega>><<nc.powered>>_EM = Region[ {<<nc.omega>><<nc.powered>>_<<dm.conductors.keys()|join('_EM, ' + nc.omega + nc.powered + '_')>>_EM} ];
    // Polarity Groups (electrical connection of the half-turns)
    {% set pol_ = ({}) %}
    <<cc_macros2.generate_polarity_groups(dm, rm_EM,aux,pol_)>>
    {% if dm.magnet.solve.thermal.solve_type %}
    // Half-Turn Conductors Groups for TH
    <<nc.omega>><<nc.powered>>_TH = Region[ {<<nc.omega>><<nc.powered>>_<<dm.conductors.keys()|join('_TH, ' + nc.omega + nc.powered + '_')>>_TH} ];
    {% endif %}
    {% if dm.magnet.geometry.electromagnetics.with_wedges %}
    // Wedges' Group for EM
    <<nc.omega>><<nc.induced>>_EM = Region[ {
                {%- if rm_EM.induced['r1_a1'].vol.names %}<<rm_EM.induced['r1_a1'].vol.names|join(', ')>>{% endif %}
                {% if rm_EM.induced['r1_a2'].vol.names %}, <<rm_EM.induced['r1_a2'].vol.names|join(', ')>>{% endif %}
                {% if rm_EM.induced['r2_a1'].vol.names %}, <<rm_EM.induced['r2_a1'].vol.names|join(', ')>>{% endif %}
                {% if rm_EM.induced['r2_a2'].vol.names %}, <<rm_EM.induced['r2_a2'].vol.names|join(', ')>>{% endif %}} ];
    {% endif %}
    {% if dm.magnet.solve.thermal.solve_type %}
        {% if dm.magnet.geometry.thermal.with_wedges %}    
    // Wedges' Group for TH
    <<nc.omega>><<nc.induced>>_TH = Region[ {
                {%- if rm_TH.induced['r1_a1'].vol.names %}<<rm_TH.induced['r1_a1'].vol.names|join(', ')>>{% endif %}
                {% if rm_TH.induced['r1_a2'].vol.names %}, <<rm_TH.induced['r1_a2'].vol.names|join(', ')>>{% endif %}
                {% if rm_TH.induced['r2_a1'].vol.names %}, <<rm_TH.induced['r2_a1'].vol.names|join(', ')>>{% endif %}
                {% if rm_TH.induced['r2_a2'].vol.names %}, <<rm_TH.induced['r2_a2'].vol.names|join(', ')>>{% endif %}} ];
        {% endif %}
    {% endif %}

    // Iron Yoke Group for EM
    {% for area in areas_to_build['EM']%}
    <<nc.omega>><<nc[area]>>_EM = Region[ {S<<nc[area]>>_<<rm_EM[area].vol.names|join(', ')>>} ];
    {% endfor %}
    {% if dm.magnet.solve.thermal.solve_type %}
    // Iron Yoke Group for TH
        {% for area in areas_to_build['TH']%}
    <<nc.omega>><<nc[area]>>_TH = Region[{S<<nc[area]>>_<<rm_TH[area].vol.names|join(', ')>>_TH}];
        {% endfor %}
        {% if dm.magnet.mesh.thermal.reference.enabled%}
    // reference 
    <<nc.omega>>_refmesh_TH = Region[ {S_refmesh_<<rm_TH.ref_mesh.vol.names|join(', ')>>_TH}];
        {% endif %}
    {% endif %}
    // Conductor group (Powered + Induced) for EM
    <<nc.omega>><<nc.conducting>>_EM = Region[ {<<nc.omega>><<nc.powered>>_EM{% if 'iron_yoke' in areas_to_build['EM'] %}, <<nc.omega>><<nc.iron_yoke>>_EM{% endif %}
                {% if dm.magnet.geometry.electromagnetics.with_wedges %}, <<nc.omega>><<nc.induced>>_EM{% endif %}} ];
    {% if dm.magnet.solve.thermal.solve_type %}
    // Conductor group (Powered + Induced) for TH
    <<nc.omega>><<nc.conducting>>_TH = Region[ {<<nc.omega>><<nc.powered>>_TH{% if 'iron_yoke' in areas_to_build['TH'] %}, <<nc.omega>><<nc.iron_yoke>>_TH{% endif %}
                {% if dm.magnet.geometry.thermal.with_wedges %}, <<nc.omega>><<nc.induced>>_TH{% endif %}} ];
        {% if not dm.magnet.geometry.thermal.use_TSA %}
    // Insulator group (TSA) for TH
    <<nc.omega>><<nc.insulator>>_TH = Region[ {<<rm_TH.insulator.vol.names|join(', ')>>} ];
        {% endif %}
    {% endif %}
    // EM Domain
    <<nc.omega>>_EM = Region[ {<<rm_EM.air.vol.name>>, <<rm_EM.air_far_field.vol.names[0]>>, <<nc.omega>><<nc.powered>>_EM{% for area in areas_to_build['EM'] %}, <<nc.omega>><<nc[area]>>_EM{% endfor %}
                {% if dm.magnet.geometry.electromagnetics.with_wedges %}, <<nc.omega>><<nc.induced>>_EM{% endif %}} ];
    {% if dm.magnet.solve.thermal.solve_type %}
    // TH Domain
    <<nc.omega>>_TH = Region[ {<<nc.omega>><<nc.powered>>_TH{% for area in areas_to_build['TH'] %}, <<nc.omega>><<nc[area]>>_TH{% endfor %}
                {% if dm.magnet.geometry.thermal.with_wedges %}, <<nc.omega>><<nc.induced>>_TH{% endif %}
                {% if not dm.magnet.geometry.thermal.use_TSA %}, <<nc.omega>><<nc.insulator>>_TH{% endif %}
                {% if dm.magnet.mesh.thermal.reference.enabled%},  <<nc.omega>>_refmesh_TH{% endif %} }];
    <<nc.omega>>_noninsulation_areas_TH  = Region[ {<<nc.omega>><<nc.powered>>_TH{% if dm.magnet.geometry.thermal.with_wedges %}, <<nc.omega>><<nc.induced>>_TH{% endif %}{% for area in areas_to_build['TH'] %}, <<nc.omega>><<nc[area]>>_TH{% endfor %}}];
    {% endif %} 
    {% if not dm.magnet.geometry.thermal.use_TSA %}
    // additional help segment (see integration and insulators)
    <<nc.omega>>_TH_not<<nc.powered>> = Region[{<<nc.omega>><<nc.insulator>>_TH {% if 'collar' in areas_to_build['TH'] %}, <<nc.omega>><<nc.collar>>_TH {% endif %}{% if dm.magnet.mesh.thermal.reference.enabled%}, <<nc.omega>>_refmesh_TH {% endif %}}];
    {% endif %} 
    // Boundary of Air Far Field   
    <<nc.boundary>><<nc.omega>> = Region[ {<<rm_EM.air_far_field.surf.name>>{% if rm_EM.boundaries.symmetry.normal_free.number %}, <<rm_EM.boundaries.symmetry.normal_free.name>>{% endif %}}];

    {% set jcZero_ht = {} %}
    {% for cond_name in dm.conductors.keys() %}
      {% do jcZero_ht.update({cond_name: []}) %}
    {% endfor %}
    {% if dm.magnet.solve.thermal.solve_type %}
        {% for turn in dm.magnet.solve.thermal.jc_degradation_to_zero.turns %}
    jcZero_ht<<turn>> = Region[{ht<<turn>>_TH}];
            {% for cond_name in dm.conductors.keys() %}
                {% if 'ht' + str(turn) + '_TH' in rm_TH.powered['r1_a1'].conductors[cond_name] + rm_TH.powered['r1_a2'].conductors[cond_name] + rm_TH.powered['r2_a1'].conductors[cond_name] + rm_TH.powered['r2_a2'].conductors[cond_name] %}
                    {% do jcZero_ht.update({cond_name: jcZero_ht[cond_name] + ['ht' + str(turn) + '_TH']}) %}
                {% endif %}
            {% endfor %}
        {% endfor %}
    {% endif %}
    {% for cond_name in dm.conductors.keys() %}
      jcNonZero_<<cond_name>> = Region[<<nc.omega>><<nc.powered>>_<<cond_name>>_EM];
        {% if dm.magnet.solve.thermal.solve_type %}
      jcNonZero_<<cond_name>> += Region[<<nc.omega>><<nc.powered>>_<<cond_name>>_TH];
      jcZero_<<cond_name>> = Region[{<<jcZero_ht[cond_name]|join(', ')>>}];
      jcNonZero_<<cond_name>> -= Region[jcZero_<<cond_name>>];
        {% endif %}
    {% endfor %}

    {% if dm.magnet.solve.thermal.solve_type %}
        {% if dm.magnet.geometry.thermal.use_TSA %}
    // --------------------- BARE ------------------------------------------------
    // physical regions of the bare blocks
    For i In {1:2}
    For j In {1:2}
        Bare~{i}~{j} = Region[ bare~{i}~{j} ];
        <<nc.omega>>_TH     += Region[ bare~{i}~{j} ];
    EndFor
    EndFor
    // ------------------- SHELLS ------------------------------------------------
    For i In {1:2}
    For j In {1:2}
        // integration domains
        Bare_Layers~{i}~{j}  = Region[ bare_layers~{i}~{j} ];
        Bare_Layers~{i}~{j} += Region[ bndDir~{i}~{j} ];
        Bare_Layers~{i}~{j} += Region[ bndNeu~{i}~{j} ];
        Bare_Layers~{i}~{j} += Region[ bndRobin~{i}~{j} ];

        Bare_Layers~{i}~{j} += Region[ QH~{i}~{j} ];

        Domain_Insulated_Str~{i}~{j} = Region[ { Bare~{i}~{j},
        Bare_Layers~{i}~{j} } ];

        midLayers~{i}~{j} = Region[midLayers~{i}~{j}];
    EndFor
    EndFor
    midLayers = Region[midLayers];
    {% if dm.magnet.geometry.thermal.use_TSA_new %} 
    midLayers_col_2_1 = Region[{<<rm_TH.thin_shells.ts_collar_groups['2_1']|join(',')>>}];
    midLayers_col_1_1 = Region[{<<rm_TH.thin_shells.ts_collar_groups['1_1']|join(',')>>}];
    midLayers_col_1_2 = Region[{<<rm_TH.thin_shells.ts_collar_groups['1_2']|join(',')>>}];
    midLayers_col_2_2 = Region[{<<rm_TH.thin_shells.ts_collar_groups['2_2']|join(',')>>}];
    midLayers_col = Region[{midLayers_col_1_1, midLayers_col_2_1, midLayers_col_1_2, midLayers_col_2_2}];

    midLayers_pol_2_1 = Region[{<<(rm_TH.thin_shells.ts_pole_groups['a_2_1']+rm_TH.thin_shells.ts_pole_groups['r_2_1'])|join(',')>>}];
    midLayers_pol_1_1 = Region[{<<(rm_TH.thin_shells.ts_pole_groups['a_1_1']+rm_TH.thin_shells.ts_pole_groups['r_1_1'])|join(',')>>}];
    midLayers_pol_1_2 = Region[{<<(rm_TH.thin_shells.ts_pole_groups['a_1_2']+rm_TH.thin_shells.ts_pole_groups['r_1_2'])|join(',')>>}];
    midLayers_pol_2_2 = Region[{<<(rm_TH.thin_shells.ts_pole_groups['a_2_2']+rm_TH.thin_shells.ts_pole_groups['r_2_2'])|join(',')>>}];
    midLayers_pol = Region[{<<rm_TH.thin_shells.poles.thin_shells| map('join', ',') |join(',') >>}]; // equivalent to Region[{midLayers_pol_1_1, midLayers_pol_2_1, midLayers_pol_1_2, midLayers_pol_2_2}];

    {% set midLayers_col = list(rm_TH.thin_shells.ts_collar_groups['1_1']) + list(rm_TH.thin_shells.ts_collar_groups['2_1']) + list(rm_TH.thin_shells.ts_collar_groups['1_2']) + list(rm_TH.thin_shells.ts_collar_groups['2_2'])%}
    {% set midLayers_a_pol = list(rm_TH.thin_shells.ts_pole_groups['a_1_1']) + list(rm_TH.thin_shells.ts_pole_groups['a_2_1']) + list(rm_TH.thin_shells.ts_pole_groups['a_1_2']) + list(rm_TH.thin_shells.ts_pole_groups['a_2_2'])%}
    {% set midLayers_r_pol = list(rm_TH.thin_shells.ts_pole_groups['r_1_1']) + list(rm_TH.thin_shells.ts_pole_groups['r_2_1']) + list(rm_TH.thin_shells.ts_pole_groups['r_1_2']) + list(rm_TH.thin_shells.ts_pole_groups['r_2_2'])%}
    {% endif %}
            {% set materials_tsa_layers = [[], []] %}
            {% set bndDir_1 = list(set(rm_TH.boundaries.thermal.temperature.groups['r1_a1']).intersection(bare_layers_2_1)) +
                        list(set(rm_TH.boundaries.thermal.temperature.groups['r2_a1']).intersection(bare_layers_1_1)) +
                        list(set(rm_TH.boundaries.thermal.temperature.groups['r1_a2']).intersection(bare_layers_2_2)) +
                        list(set(rm_TH.boundaries.thermal.temperature.groups['r2_a2']).intersection(bare_layers_1_2)) %}

            {% set bndDir_2 = list(set(rm_TH.boundaries.thermal.temperature.groups['r1_a1']).intersection(bare_layers_1_2)) +
                        list(set(rm_TH.boundaries.thermal.temperature.groups['r2_a1']).intersection(bare_layers_2_2)) +
                        list(set(rm_TH.boundaries.thermal.temperature.groups['r1_a2']).intersection(bare_layers_1_1)) +
                        list(set(rm_TH.boundaries.thermal.temperature.groups['r2_a2']).intersection(bare_layers_2_1)) %}
    {% for nr, tags in enumerate(rm_TH.thin_shells.insulation_types.thin_shells + rm_TH.thin_shells.quench_heaters.thin_shells + rm_TH.thin_shells.collar.thin_shells + rm_TH.thin_shells.poles.thin_shells) %}
    {% if dm.magnet.geometry.thermal.use_TSA_new %}
    intDomain_1_<<nr + 1>> = Region[{<<set(midLayers_1 + midLayers_a_pol).intersection(tags)|join(', ')>>}]; // normals azimuthal
    intDomain_2_<<nr + 1>> = Region[{<<set(midLayers_2 + midLayers_r_pol + midLayers_col).intersection(tags)|join(', ')>>}]; // normals radial
    {% else %}
    intDomain_1_<<nr + 1>> = Region[{<<set(midLayers_1).intersection(tags)|join(', ')>>}];
    intDomain_2_<<nr + 1>> = Region[{<<set(midLayers_2).intersection(tags)|join(', ')>>}];
    {% endif %}
    // these boundary conditions are only applied to sides without a thermal shell approximation
    // add Robin boundary conditions
    intDomain_1_<<nr + 1>> += Region[{<<set(bndRobinInt_1_1_1 + bndRobinInt_1_1_2 + bndRobinInt_1_2_1 + bndRobinInt_1_2_2).intersection(tags)|join(', ')>>}];
    intDomain_2_<<nr + 1>> += Region[{<<set(bndRobinInt_2_1_1 + bndRobinInt_2_1_2 + bndRobinInt_2_2_1 + bndRobinInt_2_2_2).intersection(tags)|join(', ')>>}];

    // add Dirichlet boundary conditions
    intDomain_1_<<nr + 1>> += Region[{<<set(bndDir_1).intersection(tags)|join(', ')>>}];
    intDomain_2_<<nr + 1>> += Region[{<<set(bndDir_2).intersection(tags)|join(', ')>>}];

    // add Neumann boundary conditions
    intDomain_1_<<nr + 1>> += Region[{<<set(bndNeuInt_1_1_1 + bndNeuInt_1_1_2 + bndNeuInt_1_2_1 + bndNeuInt_1_2_2).intersection(tags)|join(', ')>>}];
    intDomain_2_<<nr + 1>> += Region[{<<set(bndNeuInt_2_1_1 + bndNeuInt_2_1_2 + bndNeuInt_2_2_1 + bndNeuInt_2_2_2).intersection(tags)|join(', ')>>}];

    // Robin domains 
    bndRobinInt_1_1_1_<<nr + 1>> = Region[{<<set(bndRobinInt_1_1_1).intersection(tags)|join(', ')>>}];
    bndRobinInt_1_1_2_<<nr + 1>> = Region[{<<set(bndRobinInt_1_1_2).intersection(tags)|join(', ')>>}];
    bndRobinInt_1_2_1_<<nr + 1>> = Region[{<<set(bndRobinInt_1_2_1).intersection(tags)|join(', ')>>}];
    bndRobinInt_1_2_2_<<nr + 1>> = Region[{<<set(bndRobinInt_1_2_2).intersection(tags)|join(', ')>>}];
    bndRobinInt_2_1_1_<<nr + 1>> = Region[{<<set(bndRobinInt_2_1_1).intersection(tags)|join(', ')>>}];
    bndRobinInt_2_1_2_<<nr + 1>> = Region[{<<set(bndRobinInt_2_1_2).intersection(tags)|join(', ')>>}];
    bndRobinInt_2_2_1_<<nr + 1>> = Region[{<<set(bndRobinInt_2_2_1).intersection(tags)|join(', ')>>}];
    bndRobinInt_2_2_2_<<nr + 1>> = Region[{<<set(bndRobinInt_2_2_2).intersection(tags)|join(', ')>>}];

    // Neumann domains
    bndNeuInt_1_1_1_<<nr + 1>> = Region[{<<set(bndNeuInt_1_1_1).intersection(tags)|join(', ')>>}];
    bndNeuInt_1_1_2_<<nr + 1>> = Region[{<<set(bndNeuInt_1_1_2).intersection(tags)|join(', ')>>}];
    bndNeuInt_1_2_1_<<nr + 1>> = Region[{<<set(bndNeuInt_1_2_1).intersection(tags)|join(', ')>>}];
    bndNeuInt_1_2_2_<<nr + 1>> = Region[{<<set(bndNeuInt_1_2_2).intersection(tags)|join(', ')>>}];
    bndNeuInt_2_1_1_<<nr + 1>> = Region[{<<set(bndNeuInt_2_1_1).intersection(tags)|join(', ')>>}];
    bndNeuInt_2_1_2_<<nr + 1>> = Region[{<<set(bndNeuInt_2_1_2).intersection(tags)|join(', ')>>}];
    bndNeuInt_2_2_1_<<nr + 1>> = Region[{<<set(bndNeuInt_2_2_1).intersection(tags)|join(', ')>>}];
    bndNeuInt_2_2_2_<<nr + 1>> = Region[{<<set(bndNeuInt_2_2_2).intersection(tags)|join(', ')>>}];
            {% endfor %}
        {% else %} {# not TSA #}
            {% for nr, names in enumerate(rm_TH.boundaries.thermal.temperature.bc.names) %}
    <<list(dm.magnet.solve.thermal.overwrite_boundary_conditions.temperature)[nr]>> = Region[ {<<names|join(', ')>>} ];
            {% endfor %}
            {% for nr, names in enumerate(rm_TH.boundaries.thermal.heat_flux.bc.names) %}
                {% if dm.magnet.solve.thermal.He_cooling.sides != 'external' and nr == 0 %}
    general_adiabatic = Region[ {<<names|join(', ')>>} ];
                {% else %}
    <<list(dm.magnet.solve.thermal.overwrite_boundary_conditions.heat_flux)[nr - 1 if dm.magnet.solve.thermal.He_cooling.sides != 'external' else nr]>> = Region[ {<<names|join(', ')>>} ];
                {% endif %}
            {% endfor %}
            {% for nr, names in enumerate(rm_TH.boundaries.thermal.cooling.bc.names) %}
                {% if dm.magnet.solve.thermal.He_cooling.enabled and nr == 0 %}
    general_cooling = Region[ {<<names|join(', ')>>} ];
                {% else %}
    <<list(dm.magnet.solve.thermal.overwrite_boundary_conditions.cooling)[nr - 1 if dm.magnet.solve.thermal.He_cooling.enabled else nr]>> = Region[ {<<names|join(', ')>>} ];
                {% endif %}
            {% endfor %}
    Bnds_dirichlet = Region[ {<<dm.magnet.solve.thermal.overwrite_boundary_conditions.temperature|join(', ')>>} ];
    Bnds_neumann = Region[ {} ];
            {% if dm.magnet.solve.thermal.He_cooling.sides != 'external' %}
    Bnds_neumann += Region[ general_adiabatic ];
            {% endif %}
            {% if dm.magnet.solve.thermal.overwrite_boundary_conditions.heat_flux %} 
    Bnds_neumann += Region[ {<<dm.magnet.solve.thermal.overwrite_boundary_conditions.heat_flux|join(', ')>>} ];
            {% endif %}
      
    Bnds_robin = Region[ {} ];
            {% if dm.magnet.solve.thermal.He_cooling.enabled %}
    Bnds_robin += Region[ general_cooling ];
            {% endif %}
            {% if dm.magnet.solve.thermal.overwrite_boundary_conditions.cooling %}
    Bnds_robin += Region[ {<<dm.magnet.solve.thermal.overwrite_boundary_conditions.cooling|join(', ')>>} ];
            {% endif %}
    Bnds_support = Region[ {Bnds_neumann, Bnds_robin{% if dm.magnet.solve.thermal.collar_cooling.enabled %}, bndCollarGaps{% endif %}} ];
        {% endif %}
    <<rm_TH.projection_points.name>> = Region[ <<rm_TH.projection_points.number>> ];
    <<cc_macros2.generate_polarity_groups_TH(dm,aux,rm_EM,rm_TH)>>
    {% endif %}

    {% if dm.circuit.field_circuit %}
    // Power supply & Circuit Regions 
        {% set flag_active = ({}) %}
        {% set regions_CC = ({}) %}
        {% set CLIQ_dict= {"Units": 0,"groups": [],  "leads": [], "Comp":[]    } %}
        {% set ECLIQ_dict={"Units": 0,"groups": [], "leads": [], "Comp":[]     } %}
        {% set ESC_dict=  {"Units": 0 ,"groups": [],  "leads": [], "Comp":[]   } %}
        {% set init_ht = 0 %}
        {% set end_ht =  len(dm.magnet.solve.coil_windings.electrical_pairs.overwrite_electrical_order)%}
        {% set flag_R = 0 -%}
        {% set CC_dict = [] %}
    <<cc_macros2.regions_FCC(dm,rm_EM,flag_active,regions_CC,end_ht,CLIQ_dict,ECLIQ_dict,ESC_dict,CC_dict,aux)>>
    <<cc_macros2.groups_FCC(dm,rm_EM, flag_active,CLIQ_dict,ECLIQ_dict,ESC_dict,CC_dict,aux) >>
    {%if dm.magnet.solve.thermal.solve_type and flag_active['ECLIQ']%}
    Omega_p_TH_r -= Region[Omega_ECLIQ_ht_TH];
    Omega_p_TH_l -= Region[Omega_ECLIQ_ht_TH];
    {% endif %}
    {% endif %}
    {%if dm.magnet.solve.thermal.solve_type and dm.quench_protection.quench_heaters.N_strips >0 and dm.quench_protection.quench_heaters.quench_propagation == '2Dx1D'%}
    QH_HT_EM = Region[{<<'ht'~dm.quench_protection.quench_heaters.iQH_toHalfTurn_To|join('_EM, ht')~'_EM'>>}];
    noQH_HT_EM = Region[<<nc.omega>><<nc.powered>>_EM];
    noQH_HT_EM -= Region[QH_HT_EM];
    QH_HT_TH = Region[{<<'ht'~dm.quench_protection.quench_heaters.iQH_toHalfTurn_To|join('_TH, ht')~'_TH'>>}];
    noQH_HT_TH = Region[<<nc.omega>><<nc.powered>>_TH];
    noQH_HT_TH -= Region[QH_HT_TH];
        {% for i in aux.half_turns.ht.keys() %}
            {% set QH_half_turns_in_block_EM = [] %}
            {% set QH_half_turns_in_block_TH = [] %}
            {% for ht in aux.half_turns.ht[i] %}
                {% if ht in dm.quench_protection.quench_heaters.iQH_toHalfTurn_To %}
                    {% set _ = QH_half_turns_in_block_EM.append('ht' ~ ht ~ '_EM') %}
                    {% set _ = QH_half_turns_in_block_TH.append('ht' ~ ht ~ '_TH') %}
                {% endif %}
            {% endfor %}
            {% set ht_names_EM = [] %}
            {% set ht_names_TH = [] %}
            {% for ht in aux.half_turns.ht[i] %}
                {% set _ = ht_names_EM.append('ht' ~ ht ~ '_EM') %}
                {% set _ = ht_names_TH.append('ht' ~ ht ~ '_TH') %}
            {% endfor %}
    Omega_Block_<<i>>_EM = Region[ { << ht_names_EM|join(', ') >> } ];
    Omega_Block_<<i>>_TH = Region[ { << ht_names_TH|join(', ') >> } ];
            {% if QH_half_turns_in_block_EM %}
    Omega_QH_<<i>>_EM = Region[ { << QH_half_turns_in_block_EM|join(', ') >> } ];
            {% endif %}
            {% if QH_half_turns_in_block_TH %}
    Omega_QH_<<i>>_TH = Region[ { << QH_half_turns_in_block_TH|join(', ') >> } ];
            {% endif %}
        {% endfor %}
    {% endif %}
    {%if dm.magnet.solve.thermal.solve_type and dm.quench_protection.e_cliq.quench_propagation == '2Dx1D'%}
    ECLIQ_HT_EM = Region[{<<'ht'~dm.quench_protection.e_cliq.iECLIQ_toHalfTurn_To|join('_EM, ht')~'_EM'>>}];
    noECLIQ_HT_EM = Region[<<nc.omega>><<nc.powered>>_EM];
    noECLIQ_HT_EM -= Region[ECLIQ_HT_EM];
    ECLIQ_HT_TH = Region[{<<'ht'~dm.quench_protection.e_cliq.iECLIQ_toHalfTurn_To|join('_TH, ht')~'_TH'>>}];
    noECLIQ_HT_TH = Region[<<nc.omega>><<nc.powered>>_TH];
    noECLIQ_HT_TH -= Region[ECLIQ_HT_TH];
        {% for i in aux.half_turns.ht.keys() %}
            {% set ECLIQ_half_turns_in_block_EM = [] %}
            {% set ECLIQ_half_turns_in_block_TH = [] %}
            {% for ht in aux.half_turns.ht[i] %}
                {% if ht in dm.quench_protection.e_cliq.iECLIQ_toHalfTurn_To %}
                    {% set _ = ECLIQ_half_turns_in_block_EM.append('ht' ~ ht ~ '_EM') %}
                    {% set _ = ECLIQ_half_turns_in_block_TH.append('ht' ~ ht ~ '_TH') %}
                {% endif %}
            {% endfor %}
            {% set ht_names_EM = [] %}
            {% set ht_names_TH = [] %}
            {% for ht in aux.half_turns.ht[i] %}
                {% set _ = ht_names_EM.append('ht' ~ ht ~ '_EM') %}
                {% set _ = ht_names_TH.append('ht' ~ ht ~ '_TH') %}
            {% endfor %}
    Omega_Block_<<i>>_EM = Region[ { << ht_names_EM|join(', ') >> } ];
    Omega_Block_<<i>>_TH = Region[ { << ht_names_TH|join(', ') >> } ];
            {% if ECLIQ_half_turns_in_block_EM %}
    Omega_ECLIQ_<<i>>_EM = Region[ { << ECLIQ_half_turns_in_block_EM|join(', ') >> } ];
            {% endif %}
            {% if ECLIQ_half_turns_in_block_TH %}
    Omega_ECLIQ_<<i>>_TH = Region[ { << ECLIQ_half_turns_in_block_TH|join(', ') >> } ];
            {% endif %}
        {% endfor %}
    {% endif %}
}

Function {
    //------------------------ EM ------------------------------------------------
    // TODO: Hardcoded, change to mat func.
    mu0 = 4 * Pi * 1E-7;
    nuBH_air[] = 1/mu0;
    dnuBH_air[] = 0;
    nuAl[] = 1/1256e-9;
    dnuAl[] = 0;
    nu [ Region[{<<rm_EM.air.vol.name>>, <<nc.omega>><<nc.powered>>_EM, <<rm_EM.air_far_field.vol.names[0]>>{% if dm.magnet.geometry.electromagnetics.with_wedges %}, <<nc.omega>><<nc.induced>>_EM{% endif %}}] ]  = 1. / mu0;

    {% for area in areas_to_build['EM'] %}
        {% for name in rm_EM[area].vol.names %}
    nu [ <<nc.omega>><<nc[area]>>_EM ]  = nu<<name>>[$1];
    dnu_db [ <<nc.omega>><<nc[area]>>_EM ]  = dnu<<name>>[$1];
        {% endfor %}
    {% endfor %}
// Stranded conductor
    Ns=<<len(rm_EM.powered['r1_a1'].vol.names + rm_EM.powered['r1_a2'].vol.names + rm_EM.powered['r2_a1'].vol.names + rm_EM.powered['r2_a2'].vol.names)>>/10000;
    pre_eddy[]=$Time <= {% if SIM_MODE == 'Th_Mag_sta'%} <<dm.magnet.solve.thermal.time_stepping.initial_time>>{% elif SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' %} <<dm.magnet.solve.time_stepping.initial_time>>{% else %}<<dm.magnet.solve.electromagnetics.time_stepping.initial_time>>{% endif %}?0:1;
    
    {% if dm.magnet.geometry.thermal.use_TSA_new %}
    // Correction factors for the thin shells collar
        {% for nr, factor in enumerate(rm_TH.thin_shells.insulation_types.correction_factors + rm_TH.thin_shells.quench_heaters.correction_factors + rm_TH.thin_shells.collar.correction_factors + rm_TH.thin_shells.poles.correction_factors) %}
    TSA_new_correction_1_<<nr+1>> = <<factor>>; // for shells in azimuthal direction
    TSA_new_correction_2_<<nr+1>> = <<factor>>; 
        {% endfor %}
    {% endif %}

    {% if dm.magnet.solve.thermal.collar_cooling.enabled %}
    T_ref = <<rm_TH.boundaries.thermal.collar.bc.values[1]>>;
        {% if isinstance(rm_TH.boundaries.thermal.collar.bc.values[0], str) %}
    col_heatExchCoeff[] = <<rm_TH.boundaries.thermal.collar.bc.values[0]>>[$1, $2];
        {% else %}
    col_heatExchCoeff[] = <<rm_TH.boundaries.thermal.collar.bc.values[0]>>;
        {% endif %}
    {% endif %}

    // Area fct for 2D
    {% for name, current, number in zip(rm_EM.powered['r1_a1'].vol.names + rm_EM.powered['r1_a2'].vol.names + rm_EM.powered['r2_a1'].vol.names + rm_EM.powered['r2_a2'].vol.names,
                                        rm_EM.powered['r1_a1'].vol.currents + rm_EM.powered['r1_a2'].vol.currents + rm_EM.powered['r2_a1'].vol.currents + rm_EM.powered['r2_a2'].vol.currents,
                                        rm_EM.powered['r1_a1'].vol.numbers + rm_EM.powered['r1_a2'].vol.numbers + rm_EM.powered['r2_a1'].vol.numbers + rm_EM.powered['r2_a2'].vol.numbers
                                        ) %}
    area_fct[ <<name>> ] = SurfaceArea[]{ <<number>> };
    {% endfor %}

    {%  if dm.circuit.field_circuit%}
    <<cc_macros2.function_FCC(nc,dm,rm_EM, flag_active,CLIQ_dict,ECLIQ_dict,ESC_dict,CC_dict,aux)>>
    {%  endif %}
    // Generate the sign function to impose polarity of current going through the half-turns
    {% set polarities = dm.magnet.solve.coil_windings.polarities_in_group %}
    {% if len(polarities)>0 %}
        {% for i in range(polarities | length) %}
            {% set polarity = polarities[i] %}
            {% set half_turns = aux.half_turns.ht[i+1] %}
            {% for half_turn in half_turns %}
    sign_fct[<<'ht' ~ half_turn ~ '_EM'>> ] = <<polarity>>;
            {% endfor %}
        {% endfor %}
    {% else %}
        {% for name, current, number in zip(rm_EM.powered['r1_a1'].vol.names + rm_EM.powered['r1_a2'].vol.names + rm_EM.powered['r2_a1'].vol.names + rm_EM.powered['r2_a2'].vol.names,
        rm_EM.powered['r1_a1'].vol.currents + rm_EM.powered['r1_a2'].vol.currents + rm_EM.powered['r2_a1'].vol.currents + rm_EM.powered['r2_a2'].vol.currents,
        rm_EM.powered['r1_a1'].vol.numbers + rm_EM.powered['r1_a2'].vol.numbers + rm_EM.powered['r2_a1'].vol.numbers + rm_EM.powered['r2_a2'].vol.numbers
        ) %}
    sign_fct[ <<name>> ] = Sign[<<current>>];    
        {% endfor %}
    {% endif %}
    {% if  not dm.circuit.field_circuit%}
    i_fct[] =InterpolationLinear[$Time]{List[{
    {%- for t, i in zip(dm.power_supply.t_control_LUT, dm.power_supply.I_control_LUT) -%}
      << t >>, << i >>{% if not loop.last %}, {% endif %}
    {%- endfor -%}
    }]};
    {% endif %}
    {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Th_Mag_sta' %}
    //------------------------ TH ------------------------------------------------
    // 2D Areas in TH
    {% for name, number in zip(rm_TH.powered['r1_a1'].vol.names + rm_TH.powered['r1_a2'].vol.names + rm_TH.powered['r2_a1'].vol.names + rm_TH.powered['r2_a2'].vol.names,
                                    rm_TH.powered['r1_a1'].vol.numbers + rm_TH.powered['r1_a2'].vol.numbers + rm_TH.powered['r2_a1'].vol.numbers + rm_TH.powered['r2_a2'].vol.numbers
                                    ) %}
    area_fct[ <<name>> ] = SurfaceArea[]{ <<number>> };
        {% endfor %}
            {% if dm.magnet.geometry.thermal.with_wedges %}
                {% for name, number in zip(rm_TH.induced['r1_a1'].vol.names + rm_TH.induced['r1_a2'].vol.names + rm_TH.induced['r2_a1'].vol.names + rm_TH.induced['r2_a2'].vol.names, rm_TH.induced['r1_a1'].vol.numbers + rm_TH.induced['r1_a2'].vol.numbers + rm_TH.induced['r2_a1'].vol.numbers + rm_TH.induced['r2_a2'].vol.numbers) %}
    area_fct[ <<name>> ] = SurfaceArea[]{ <<number>> };
                {% endfor %}
            {% endif %}
  
            {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Th_Mag_sta' %}
    //Piecewise Temp function for coupled sim
    {% if dm.magnet.geometry.electromagnetics.with_wedges%}
    {% set T_regions = rm_EM.powered['r1_a1'].vol.numbers + rm_EM.powered['r2_a1'].vol.numbers + rm_EM.powered['r1_a2'].vol.numbers + rm_EM.powered['r2_a2'].vol.numbers + rm_EM.induced['r1_a1'].vol.numbers + rm_EM.induced['r2_a1'].vol.numbers + rm_EM.induced['r1_a2'].vol.numbers + rm_EM.induced['r2_a2'].vol.numbers %}
    {% else %}
    {% set T_regions =rm_EM.powered['r1_a1'].vol.numbers + rm_EM.powered['r2_a1'].vol.numbers + rm_EM.powered['r1_a2'].vol.numbers + rm_EM.powered['r2_a2'].vol.numbers %}
    {% endif %}
    // Temperature function per Half-turn for EM
                {% for idx, phy_elem in enumerate(T_regions) %}
    T_EM_fct[Region[<<phy_elem>>]] = $T_a_<<idx>>;
                {% endfor %}
    // Current function per Half-turn for TH (will need to be revised for DISCC)
    I2TH_fct[Region[<<nc.omega>><<nc.powered>>_TH_r]] = Abs[CompZ[$I2TH_1]];
    I2TH_fct[Region[<<nc.omega>><<nc.powered>>_TH_l]] = Abs[CompZ[$I2TH_2]];
    {% for i,ht in enumerate(aux.half_turns.ADD_COILS) %}
    I2TH_fct[Region[<<'ht'~ht~'_TH'>>]]= Abs[CompZ[$I2TH_<<i+3>>]] ;
    {% endfor %}
    {% else %}
    I2TH_fct[Region[<<nc.omega>><<nc.powered>>_TH_r]] = <<dm.power_supply.I_control_LUT[0]>>;
    I2TH_fct[Region[<<nc.omega>><<nc.powered>>_TH_l]] = <<dm.power_supply.I_control_LUT[0]>>;
            {% endif %}
    {% endif %}
    // --------------- MATERIAL FUNCTIONS ----------------------------------------
        {% set resistivityMacroName = {'Cu': 'MATERIAL_Resistivity_Copper_T_B',
                                'CFUN_rhoCu_NIST': 'MATERIAL_Resistivity_Copper_T_B',
                                'Ag': 'MATERIAL_Resistivity_Silver_T_B',
                                'SS': 'MATERIAL_Resistivity_SSteel_T',
                                'BHiron8': 'MATERIAL_Resistivity_SSteel_T',
                                'Al': 'MATERIAL_Resistivity_Aluminum_T'
                            } -%}
        {% set criticalCurrentDensityMacroName = {'Nb-Ti_CUDI1': 'MATERIAL_CriticalCurrentDensity_NiobiumTitanium_CUDI1_T_B',
                                'Nb3Sn_Summers': 'MATERIAL_CriticalCurrentDensity_Niobium3Tin_Summers_T_B',
                                'Nb3Sn_Bordini': 'MATERIAL_CriticalCurrentDensity_Niobium3Tin_Bordini_T_B',
                                'BSCCO2212': 'MATERIAL_CriticalCurrentDensity_BSCCO2212_BSCCO_2212_LBNL_T_B'} %}
        {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Th_Mag_sta' %}                                
            {% set thermalConductivityMacroName = {'Cu': 'MATERIAL_ThermalConductivity_Copper_T_B',
                                           'CFUN_kCu_NIST': 'MATERIAL_ThermalConductivity_Copper_T_B',
                                           'Ag': 'MATERIAL_ThermalConductivity_Silver_T', 'SS': 'MATERIAL_ThermalConductivity_SSteel_T',
                                           'BHiron8':  'MATERIAL_ThermalConductivity_SSteel_T',
                                           'kapton': 'MATERIAL_ThermalConductivity_Kapton_T', 'G10': 'MATERIAL_ThermalConductivity_G10_T',
                                            'Al': 'MATERIAL_ThermalConductivity_Aluminum_T', 'BHiron2': 'MATERIAL_ThermalConductivity_BHiron2_T'} %} 
            {% set specificHeatCapacityMacroName = {'Cu': 'MATERIAL_SpecificHeatCapacity_Copper_T',
                                            'CFUN_CvCu_NIST': 'MATERIAL_SpecificHeatCapacity_Copper_T',
                                            'Ag': 'MATERIAL_SpecificHeatCapacity_Silver_T',
                                            'SS': 'MATERIAL_SpecificHeatCapacity_SSteel_T',
                                            'BHiron8': 'MATERIAL_SpecificHeatCapacity_SSteel_T',
                                            'Nb-Ti': 'MATERIAL_SpecificHeatCapacity_NiobiumTitanium_T_B_I',
                                            'Nb3Sn': 'MATERIAL_SpecificHeatCapacity_Niobium3Tin_T_B',
                                            'BSCCO2212': 'MATERIAL_SpecificHeatCapacity_BSCCO2212_T',
                                            'kapton': 'MATERIAL_SpecificHeatCapacity_Kapton_T', 'G10': 'MATERIAL_SpecificHeatCapacity_G10_T', 
                                            'helium': 'MATERIAL_SpecificHeatCapacity_Helium_T',
                                            'Al': 'MATERIAL_SpecificHeatCapacity_Aluminum_T', 'BHiron2': 'MATERIAL_SpecificHeatCapacity_BHiron2_T'} %} 
            {% set QuenchPropVelMacroName = {'Nb-Ti': 'MATERIAL_QuenchProp_NbTi',
                                            'Nb3Sn': 'MATERIAL_QuenchProp_Nb3Sn'} %}

            {% set thermalConductivityTSAStiffnessMacroName = {'Cu': 'MATERIAL_ThermalConductivity_Copper_TSAStiffness_T_k_l', 'SS': 'MATERIAL_ThermalConductivity_SSteel_TSAStiffness_T_k_l','BHiron8': 'MATERIAL_ThermalConductivity_SSteel_TSAStiffness_T_k_l',
                                            'kapton': 'MATERIAL_ThermalConductivity_Kapton_TSAStiffness_T_k_l', 'G10': 'MATERIAL_ThermalConductivity_G10_TSAStiffness_T_k_l',
                                            'stycast': 'MATERIAL_ThermalConductivity_Stycast_TSAStiffness_T_k_l'} %}

            {% set thermalConductivityTSAMassMacroName = {'Cu': 'MATERIAL_ThermalConductivity_Copper_TSAMass_T_k_l', 'SS': 'MATERIAL_ThermalConductivity_SSteel_TSAMass_T_k_l',  'BHiron8': 'MATERIAL_ThermalConductivity_SSteel_TSAMass_T_k_l',
                                                  'kapton': 'MATERIAL_ThermalConductivity_Kapton_TSAMass_T_k_l', 'G10': 'MATERIAL_ThermalConductivity_G10_TSAMass_T_k_l',
                                                  'stycast': 'MATERIAL_ThermalConductivity_Stycast_TSAMass_T_k_l'} %}

            {% set specificHeatCapacityTSAMacroName = {'Cu': 'MATERIAL_SpecificHeatCapacity_Copper_TSAMass_T_k_l', 'SS': 'MATERIAL_SpecificHeatCapacity_SSteel_TSAMass_T_k_l','BHiron8': 'MATERIAL_SpecificHeatCapacity_SSteel_TSAMass_T_k_l',
                                               'kapton': 'MATERIAL_SpecificHeatCapacity_Kapton_TSAMass_T_k_l', 'G10': 'MATERIAL_SpecificHeatCapacity_G10_TSAMass_T_k_l',
                                               'stycast': 'MATERIAL_SpecificHeatCapacity_Stycast_TSAMass_T_k_l'} %}
        {% endif %}
        {% for name, cond in dm.conductors.items() %}
            {% if cond.cable.f_inner_voids and cond.cable.f_outer_voids %}
    f_inner_voids_<<name>> = <<cond.cable.f_inner_voids>>;
    f_outer_voids_<<name>> = <<cond.cable.f_outer_voids>>;
    f_strand_<<name>> = 1.0 - (<<cond.cable.f_inner_voids>> + <<cond.cable.f_outer_voids>>);
            {% else %}
                {% if cond.strand.type == 'Round' %}
                    {% set n_strands = cond.cable.n_strands %}
                    {% set A_Strand = cond.cable.n_strands * Pi/4.0 * cond.strand.diameter**2 %}
                {% elif cond.strand.type == 'Rectangular' %}
                    {% set n_strands = cond.cable.n_strands if cond.cable.type == 'Rutherford' else 1 %}
                    {% set A_Strand = n_strands * cond.strand.bare_width * cond.strand.bare_height %}
                {% endif %}
                {% set A_cable = cond.cable.bare_cable_width * cond.cable.bare_cable_height_mean %}

                {% set f_both_voids = 1.0 - A_Strand / A_cable %}
                {% set f_inner_voids = f_both_voids * (0.5 - 1.0/n_strands) %}
                {% set f_outer_voids = f_both_voids * (0.5 + 1.0/n_strands) %}

    f_inner_voids_<<name>> = <<f_inner_voids>>;
    f_outer_voids_<<name>> = <<f_outer_voids>>;
    f_strand_<<name>> = 1.0 - <<f_both_voids>>;
            {% endif %}

    f_stabilizer_<<name>> = f_strand_<<name>> * <<cond.strand.Cu_noCu_in_strand>> / (1. + <<cond.strand.Cu_noCu_in_strand>>);
    f_sc_<<name>> = f_strand_<<name>> * (1.0 - <<cond.strand.Cu_noCu_in_strand>> / (1. + <<cond.strand.Cu_noCu_in_strand>>));
        {% endfor %}

        {% set current_cond = namespace(conductor={}) %}
        {% for name, cond in dm.conductors.items() %}
    <<criticalCurrentDensity("jcNonZero_" + name, cond, time_trigger=1e6, cond_name=name)>>
        {% endfor %}
        {% if dm.magnet.solve.thermal.solve_type %}
            {% for turn, t_trigger in zip(dm.magnet.solve.thermal.jc_degradation_to_zero.turns, dm.magnet.solve.thermal.jc_degradation_to_zero.t_trigger) %}
                {% for name, cond in dm.conductors.items() %}
                    {% if 'ht' + str(turn) + '_TH' in jcZero_ht[name] %}
                        {% set current_cond.conductor = cond %}
                        {% set current_cond.name = name %}
                    {% endif %}
                {% endfor %}
    <<criticalCurrentDensity("jcZero_ht" + str(turn), cond=current_cond.conductor, time_trigger=t_trigger, cond_name=current_cond.name)>>
            {% endfor %}
        {% endif %}
    TestQuench[] = CFUN_quenchState_I_Ic[$3,criticalCurrentDensity[$1, $2] * area_fct[]];
    
        // Resistivity of the strands
        // -$1: Temperature [K]
        // -$2: Norm of the magnetic flux density [T]
        {% if SIM_MODE == Mag_dyn or SIM_MODE == Mag_dyn_0 or SIM_MODE == Mag_sta%}
        {% set T_sim =  dm.magnet.solve.electromagnetics.time_stepping.T_sim %}
        {% else %}
        {% set T_sim =  "$1" %}
        {% endif %}
        {% for name, cond in dm.conductors.items() %}
    rho[<<nc.omega>><<nc.powered>>_<<name>>_EM] = EffectiveResistivity[<<materials[resistivityMacroName[cond.strand.rho_material_stabilizer]](RRR=cond.strand.RRR,T=T_sim)>>]{f_stabilizer_<<name>>};
            {% if dm.magnet.solve.thermal.solve_type %}
    rho[<<nc.omega>><<nc.powered>>_<<name>>_TH] = EffectiveResistivity[<<materials[resistivityMacroName[cond.strand.rho_material_stabilizer]](RRR=cond.strand.RRR)>>]{f_stabilizer_<<name>>};
            {% endif %}
        {% endfor %}
        {% if dm.magnet.geometry.electromagnetics.with_wedges %}
    // Resistivity of the wedges
    rho[<<nc.omega>><<nc.induced>>_EM] = <<materials[resistivityMacroName[dm.magnet.solve.wedges.material]](RRR=dm.magnet.solve.wedges.RRR,T=T_sim)>>;
            {% if dm.magnet.solve.thermal.solve_type %}        
                {% if dm.magnet.geometry.thermal.with_wedges %}
    rho[<<nc.omega>><<nc.induced>>_TH] = <<materials[resistivityMacroName[dm.magnet.solve.wedges.material]](RRR=dm.magnet.solve.wedges.RRR)>>;
                {% endif %}
            {% endif %}
        {% endif %}
        {% if dm.magnet.solve.thermal.solve_type %}

        // AUX FUNCTIONS
        {% if dm.magnet.solve.thermal.solve_type %}
            {% if dm.magnet.geometry.thermal.use_TSA %}
    // --------------------- TSA BC FUNCTIONS & CONST. --------------------------------
                {% for nr, tags in enumerate(rm_TH.boundaries.thermal.temperature.bc.numbers) %}
    bnd_dirichlet_<<nr + 1>>() = {<<tags|join(', ')>>};
    val_temperature_<<nr + 1>> = <<rm_TH.boundaries.thermal.temperature.bc.value[nr]>>;
                {% endfor %}
    num_dirichlet = <<len(rm_TH.boundaries.thermal.temperature.bc.numbers)>>;  // number of different dirichlet boundary cond.

                {% for nr, tags in enumerate(rm_TH.boundaries.thermal.heat_flux.bc.numbers) %}
    bnd_neumann_<<nr + 1>>() = {<<tags|join(', ')>>};
    val_heatFlux_<<nr + 1>> = <<rm_TH.boundaries.thermal.heat_flux.bc.value[nr]>>;
                {% endfor %}
    num_neumann = <<len(rm_TH.boundaries.thermal.heat_flux.bc.numbers)>>;  // number of different neumann boundary cond.

                {% for nr, tags in enumerate(rm_TH.boundaries.thermal.cooling.bc.numbers) %}
    bnd_robin_<<nr + 1>>() = {<<tags|join(', ')>>};
                    {% if isinstance(rm_TH.boundaries.thermal.cooling.bc.values[nr][0], str) %}
    val_heatExchCoeff_<<nr + 1>>[] = <<rm_TH.boundaries.thermal.cooling.bc.values[nr][0]>>[$1, $2];
                    {% else %}
    val_heatExchCoeff_<<nr + 1>>[] = <<rm_TH.boundaries.thermal.cooling.bc.values[nr][0]>>;
                    {% endif %}
    val_Tinf_<<nr + 1>> = <<rm_TH.boundaries.thermal.cooling.bc.values[nr][1]>>;
                {% endfor %}
    num_robin = <<len(rm_TH.boundaries.thermal.cooling.bc.numbers)>>;  // number of different robin boundary cond.
    {#
    // first idx: 1 layers parallel to radial direction (== normal to phi unit vector)
    //            2 layers parallel to azimuthal direction (== normal to r unit vector)
    // second and third idx: same as bare layers
    // this gives the relation between radius/angle and index 0 to n_ele
    #}
                {% for nr, n_ele in enumerate(rm_TH.thin_shells.insulation_types.layers_number + rm_TH.thin_shells.quench_heaters.layers_number + rm_TH.thin_shells.collar.layers_number + rm_TH.thin_shells.poles.layers_number) %}
    outerElem_1_1_1_<<nr + 1>> = 0;
    outerElem_2_1_1_<<nr + 1>> = 0;
    outerElem_1_2_1_<<nr + 1>> = <<n_ele>>;
    outerElem_2_2_1_<<nr + 1>> = 0;
    outerElem_1_1_2_<<nr + 1>> = 0;
    outerElem_2_1_2_<<nr + 1>> = <<n_ele>>;
    outerElem_1_2_2_<<nr + 1>> = <<n_ele>>;
    outerElem_2_2_2_<<nr + 1>> = <<n_ele>>;
                {% endfor %}

                {% set no_flip_tags = rm_TH.thin_shells.second_group_is_next['azimuthally'] + rm_TH.thin_shells.second_group_is_next['radially'] %}
                {% set all_dir = bndDir_1 + bndDir_2 %}
                {% set all_neu = bndNeuInt_1_1_1 + bndNeuInt_1_1_2 + bndNeuInt_1_2_1 + bndNeuInt_1_2_2 + bndNeuInt_2_1_1 + bndNeuInt_2_1_2 + bndNeuInt_2_2_1 + bndNeuInt_2_2_2 %}
                {% set all_robin = bndRobinInt_1_1_1 + bndRobinInt_1_1_2 + bndRobinInt_1_2_1 + bndRobinInt_1_2_2 + bndRobinInt_2_1_1 + bndRobinInt_2_1_2 + bndRobinInt_2_2_1 + bndRobinInt_2_2_2 %}

                {% set flip_tags = list(set(rm_TH.thin_shells.mid_turns_layers_poles + all_neu + all_dir + all_robin + ns.all_QH) - set(no_flip_tags))  %}
            {% endif %}
        {% endif %}
    // Effective thermal conductivity of the bare part
    // -$1: Temperature [K]
    // -$2: Norm of the magnetic flux density [T]
            {% for name, cond in dm.conductors.items() %}
    kappa[<<nc.omega>><<nc.powered>>_<<name>>_TH] = RuleOfMixtures[
    <<materials[thermalConductivityMacroName[cond.strand.k_material_stabilizer]
        ](RRR=cond.strand.RRR)>>
                {% if cond.cable.material_inner_voids != 'helium' %}
        , <<materials[thermalConductivityMacroName[cond.cable.material_inner_voids]]()>>
                {% endif %}
                {% if cond.cable.material_outer_voids != 'helium' %}
        , <<materials[thermalConductivityMacroName[cond.cable.material_outer_voids]]()>>
                {% endif %}
        ]
        {f_stabilizer_<<name>>
                {% if cond.cable.material_inner_voids != 'helium' %}
        , f_inner_voids_<<name>>
                {% endif %}
                {% if cond.cable.material_outer_voids != 'helium' %}
        ,  f_outer_voids_<<name>>
                {% endif %}
        };
            {% endfor %}

    // Heat capacity of bare part
    // -$1: Temperature [K]
    // -$2: Norm of the magnetic flux density [T]
            {% for name, cond in dm.conductors.items() %}
                {% if cond.strand.material_superconductor == 'Nb-Ti' %}
    heatCap[<<nc.omega>><<nc.powered>>_<<name>>_TH] = RuleOfMixtures[
                <<materials[specificHeatCapacityMacroName[cond.strand.Cv_material_stabilizer]]()>>,
                <<materials[specificHeatCapacityMacroName[cond.strand.material_superconductor]](C1=cond.Jc_fit.C1_CUDI1, C2=cond.Jc_fit.C2_CUDI1, current="I2TH_fct[]")>>, 
                <<materials[specificHeatCapacityMacroName[cond.cable.material_inner_voids]]()>>,
                <<materials[specificHeatCapacityMacroName[cond.cable.material_outer_voids]]()>>
                ]
                {
                f_stabilizer_<<name>>,
                f_sc_<<name>>,
                f_inner_voids_<<name>>,
                f_outer_voids_<<name>>
                };
                {% else %}
    heatCap[<<nc.omega>><<nc.powered>>_<<name>>_TH] = RuleOfMixtures[
                <<materials[specificHeatCapacityMacroName[cond.strand.Cv_material_stabilizer]]()>>,
                <<materials[specificHeatCapacityMacroName[cond.strand.material_superconductor]]()>>,
                <<materials[specificHeatCapacityMacroName[cond.cable.material_inner_voids]]()>>,
                <<materials[specificHeatCapacityMacroName[cond.cable.material_outer_voids]]()>>
                ]
                {
                f_stabilizer_<<name>>, 
                f_sc_<<name>>,
                f_inner_voids_<<name>>, 
                f_outer_voids_<<name>>
                };
                {% endif %}
            {% endfor %}
{% if (dm.quench_protection.quench_heaters.quench_propagation == "2Dx1D" or dm.quench_protection.e_cliq.quench_propagation == "2Dx1D") and dm.magnet.solve.thermal.solve_type%}
    // Quench Propagation 2Dx1D
    {%  set counter = {"counter1": 0} %}
    {% for i in aux.half_turns.ht.keys() %}
    L_Mag[Region[{<<nc.omega>>_Block_<<i>>_EM,<<nc.omega>>_Block_<<i>>_TH}]] = <<dm.magnet.solve.coil_windings.half_turn_length[i-1]>>; // Magnetic Length [m]
            {% set QH_half_turns_in_block = [] %}
            {% set ECLIQ_half_turns_in_block = [] %}
            {% set ECLIQ_coil = [] %}
            {% for ht in aux.half_turns.ht[i] %}
                {% if ht in dm.quench_protection.quench_heaters.iQH_toHalfTurn_To and dm.quench_protection.quench_heaters.quench_propagation == "2Dx1D"%}
                    {% set _ = QH_half_turns_in_block.append('ht' ~ ht ~ '_EM') %}
                {% endif %}
                {% if ht in dm.quench_protection.e_cliq.iECLIQ_toHalfTurn_To and dm.quench_protection.e_cliq.quench_propagation == "2Dx1D"%}
                    {% set _ = ECLIQ_half_turns_in_block.append('ht' ~ ht ~ '_EM') %}
                    {% set _ = ECLIQ_coil.append(dm.quench_protection.e_cliq.iECLIQ_toHalfTurn_From[dm.quench_protection.e_cliq.iECLIQ_toHalfTurn_To.index(ht)]) %}
                {% endif %}
            {% endfor %}
            {% if QH_half_turns_in_block %}
    L_QH[Region[{Omega_QH_<<i>>_EM,Omega_QH_<<i>>_TH}]] = <<dm.quench_protection.quench_heaters.l[counter["counter1"]]>>; // QH Length [m]
    L_Cu[Region[{Omega_QH_<<i>>_EM,Omega_QH_<<i>>_TH}]] = <<dm.quench_protection.quench_heaters.l_copper[counter["counter1"]]>>; // QH Cu coil length
    L_SS[Region[{Omega_QH_<<i>>_EM,Omega_QH_<<i>>_TH}]] = <<dm.quench_protection.quench_heaters.l_stainless_steel[counter["counter1"]]>>; // QH SS coil length [m]
                {% if dm.quench_protection.quench_heaters.L_QH_offset %}
    L_QH_Offset[Region[{Omega_QH_<<i>>_EM,Omega_QH_<<i>>_TH}]] = <<dm.quench_protection.quench_heaters.L_QH_offset[counter["counter1"]]>>; // QH Length offset [m]
                {% else %}
    L_QH_Offset[Region[{Omega_QH_<<i>>_EM,Omega_QH_<<i>>_TH}]] = 0; // QH Length offset [m]
                {% endif %}
        <<cc_macros2.increment(counter, "counter1") >>   
            {% endif %}
            {% if ECLIQ_half_turns_in_block %}
        L_ECLIQ[Region[{Omega_ECLIQ_<<i>>_EM,Omega_ECLIQ_<<i>>_TH}]] = <<dm.quench_protection.e_cliq.l_ecliq[ECLIQ_coil[0]-1]>>; // ECLIQ Length [m]
        h_ECLIQ[Region[{Omega_ECLIQ_<<i>>_EM,Omega_ECLIQ_<<i>>_TH}]] = <<dm.quench_protection.e_cliq.h_ecliq[ECLIQ_coil[0]-1]>>; // ECLIQ spacing [m]
        N_ECLIQ_units[Region[{Omega_ECLIQ_<<i>>_EM,Omega_ECLIQ_<<i>>_TH}]]=<<dm.quench_protection.e_cliq.N_units[ECLIQ_coil[0]-1]>>; // Number of ECLIQs per cross-section in the 2D representation
                {% if dm.quench_protection.e_cliq.L_ecliq_offset %}
        L_ECLIQ_Offset[Region[{Omega_ECLIQ_<<i>>_EM,Omega_ECLIQ_<<i>>_TH}]] = <<dm.quench_protection.e_cliq.L_ecliq_offset[ECLIQ_coil[0]-1]>>; // ECLIQ Length offset [m]
                {% else %}
        L_ECLIQ_Offset[Region[{Omega_ECLIQ_<<i>>_EM,Omega_ECLIQ_<<i>>_TH}]] = 0; // ECLIQ Length offset [m]
                {% endif %} 
            {% endif %}
    {% endfor %}
    {% if dm.quench_protection.quench_heaters.quench_propagation == "2Dx1D" %}
    N_SS[Region[{QH_HT_EM,QH_HT_TH}]]= (L_QH[]+L_Cu[])/(L_SS[]+L_Cu[]); //Number of SS strips (where QH) [-]    
    L_strip_0[]= N_SS[]*L_SS[]; // Initial Normal Zone [m]
    {% endif %}
    {% if dm.quench_protection.e_cliq.quench_propagation == "2Dx1D" %}
    L_strip_0[]= N_ECLIQ_units[]*L_ECLIQ[]; // Initial Normal Zone [m]
    {% endif %}
    //Normal Zone Propagation Velocity
    // -$1: Temperature [K]
    // -$2: Norm of the magnetic flux density [T]
    // -$3: Current [A]
    {% if dm.quench_protection.quench_heaters.quench_prop_model == "Wilson" %}
    {% set cv_temp =  dm.magnet.solve.thermal.init_temperature %}
    {% else %}
    {% set cv_temp =  "Ts[$1,$2,$3]" %}
    {% endif %}
    {% set ECLIQ_conductors = [] %}
    {% for i in range(len(dm.magnet.solve.coil_windings.conductor_to_group)) %}
        {% if dm.magnet.solve.coil_windings.group_to_coil_section[i]>1 %}
            {% set _ = ECLIQ_conductors.append(dm.magnet.solve.coil_windings.conductor_to_group[i]) %}
        {% endif %}
    {% endfor %}
            {% for name, cond in dm.conductors.items() %}
                {% if cond.strand.material_superconductor == 'Nb-Ti' %}
    Tc[Region[{<<nc.omega>><<nc.powered>>_<<name>>_EM,<<nc.omega>><<nc.powered>>_<<name>>_TH}]]=CFUN_TcNbTi_B[$2]{{% if cond.Jc_fit.type == 'Summers' %}<<cond.Jc_fit.Tc0_Summers>>,<<cond.Jc_fit.Bc20_Summers>>{% else %}<<cond.Jc_fit.Tc0_CUDI1>>,<<cond.Jc_fit.Bc20_CUDI1>> {% endif %}}; // Critical temperature of the superconductor [K]
    Tcs[Region[{<<nc.omega>><<nc.powered>>_<<name>>_EM,<<nc.omega>><<nc.powered>>_<<name>>_TH}]]=CFUN_TcsNbTi_B_I[$2,$3]{<<cond.Jc_fit.C1_CUDI1>>,<< cond.Jc_fit.C2_CUDI1>>}; // Current sharing temperature [K]
    Ts[Region[{<<nc.omega>><<nc.powered>>_<<name>>_EM,<<nc.omega>><<nc.powered>>_<<name>>_TH}]]=(Tc[$1,$2,$3]+Tcs[$1,$2,$3])/2 ; // Avg temperature between Tc and Tcs [K]
    NZPV[Region[{<<nc.omega>><<nc.powered>>_<<name>>_EM,<<nc.omega>><<nc.powered>>_<<name>>_TH}]] = CFUN_NZPV_T[$3/area_fct[],Tcs[$1,$2,$3],Tc[$1,$2,$3], // NZPV from Suoerconducting Magnets (Wilson) [m/s]
            {% if dm.quench_protection.quench_heaters.quench_prop_model == "Wilson" %}(Tc[$1,$2,$3]^4-<<dm.magnet.solve.thermal.init_temperature>>^4)/(4*<<dm.magnet.solve.thermal.init_temperature>>^3*(Tc[$1,$2,$3]-<<dm.magnet.solve.thermal.init_temperature>>))*{% endif %}        
            RuleOfMixtures[
                <<materials[specificHeatCapacityMacroName[cond.strand.Cv_material_stabilizer]](T=cv_temp)>>,
                <<materials[specificHeatCapacityMacroName[cond.strand.material_superconductor]](C1=cond.Jc_fit.C1_CUDI1, C2=cond.Jc_fit.C2_CUDI1, current="$3",T=cv_temp)>>,
                <<materials[specificHeatCapacityMacroName[cond.cable.material_inner_voids]](T=cv_temp)>>,
                <<materials[specificHeatCapacityMacroName[cond.cable.material_outer_voids]](T=cv_temp)>>
                ]
                {
                f_stabilizer_<<name>>, 
                f_sc_<<name>>,
                f_inner_voids_<<name>>, 
                f_outer_voids_<<name>>
                }]{<<dm.magnet.solve.thermal.init_temperature>>};
                {% else %}
    Tc[Region[{<<nc.omega>><<nc.powered>>_<<name>>_EM,<<nc.omega>><<nc.powered>>_<<name>>_TH}]]=CFUN_TcNb3Sn_B[$2]{<<cond.Jc_fit.Tc0_Summers>>,<<cond.Jc_fit.Bc20_Summers>>}; // Critical temperature of the superconductor [K]
    Tcs[Region[{<<nc.omega>><<nc.powered>>_<<name>>_EM,<<nc.omega>><<nc.powered>>_<<name>>_TH}]]=CFUN_TcsNb3Sn_J_B_Jc0[$3/area_fct[],$2,CFUN_Jc_Nb3Sn_Summers_T_B[$1,$2]{<<cond.Jc_fit.Jc0_Summers>>,<<cond.Jc_fit.Tc0_Summers>>,<<cond.Jc_fit.Bc20_Summers>>}]{<<cond.Jc_fit.Jc0_Summers>>,<<cond.Jc_fit.Tc0_Summers>>,<<cond.Jc_fit.Bc20_Summers>>}; // Current sharing temperature [K]
    Ts[Region[{<<nc.omega>><<nc.powered>>_<<name>>_EM,<<nc.omega>><<nc.powered>>_<<name>>_TH}]]=(Tcs[$1,$2,$3]+Tc[$1,$2,$3])/2; // Avg temperature between Tc and Tcs [K]
    NZPV[Region[{<<nc.omega>><<nc.powered>>_<<name>>_EM,<<nc.omega>><<nc.powered>>_<<name>>_TH}]] = CFUN_NZPV_T[$3/area_fct[],CFUN_TcsNb3Sn_J_B_Jc0[$3/area_fct[],$2,CFUN_Jc_Nb3Sn_Summers_T_B[$1,$2]{<<cond.Jc_fit.Jc0_Summers>>,<<cond.Jc_fit.Tc0_Summers>>,<<cond.Jc_fit.Bc20_Summers>>}]{<<cond.Jc_fit.Jc0_Summers>>,<<cond.Jc_fit.Tc0_Summers>>,<<cond.Jc_fit.Bc20_Summers>>},CFUN_TcNb3Sn_B[$2]{<<cond.Jc_fit.Tc0_Summers>>,<<cond.Jc_fit.Bc20_Summers>>}, // NZPV from Suoerconducting Magnets (Wilson) [m/s]
                {% if dm.quench_protection.quench_heaters.quench_prop_model == "Wilson" %}(Tc[$1,$2,$3]^4-<<dm.magnet.solve.thermal.init_temperature>>^4)/(4*<<dm.magnet.solve.thermal.init_temperature>>^3*(Tc[$1,$2,$3]-<<dm.magnet.solve.thermal.init_temperature>>))*{% endif %}        
            RuleOfMixtures[
                <<materials[specificHeatCapacityMacroName[cond.strand.Cv_material_stabilizer]](T=cv_temp)>>,
                <<materials[specificHeatCapacityMacroName[cond.strand.material_superconductor]](T=cv_temp)>>,
                <<materials[specificHeatCapacityMacroName[cond.cable.material_inner_voids]](T=cv_temp)>>,
                <<materials[specificHeatCapacityMacroName[cond.cable.material_outer_voids]](T=cv_temp)>>
                ]
                {
                f_stabilizer_<<name>>, 
                f_sc_<<name>>,
                f_inner_voids_<<name>>, 
                f_outer_voids_<<name>>
                }]{<<dm.magnet.solve.thermal.init_temperature>>}; 
            {% endif %}
        {% endfor %}
    {% if dm.quench_protection.quench_heaters.quench_propagation == "2Dx1D" %}
    N_QH[QH_HT_EM] = GetVariable[ElementNum[],QuadraturePointIndex[]]{$Quench_ratio_EM}/(N_SS[]+1)>=L_Cu[]/L_Mag[] ? 2*(N_SS[] -1): 0; // Reduction of QPF if the whole QH length is already quenched (QH_EM) [-]
    N_QH[QH_HT_TH] = GetVariable[ElementNum[],QuadraturePointIndex[]]{$Quench_ratio_TH}/(N_SS[]+1)>=L_Cu[]/L_Mag[] ? 2*(N_SS[] -1): 0; // Reduction of QPF if the whole QH length is already quenched (QH_TH) [-]
    L_QH_F[Region[{QH_HT_EM,QH_HT_TH}]] = (L_Mag[]-L_QH[])/2-L_QH_Offset[]; // Front length to magnet end
    L_QH_B[Region[{QH_HT_EM,QH_HT_TH}]] = (L_Mag[]-L_QH[])/2+L_QH_Offset[]; // Back length to magnet end
    N_QH_Offset[QH_HT_EM] = GetVariable[ElementNum[],QuadraturePointIndex[]]{$Quench_ratio_EM}/(N_SS[]+1)>=L_QH_F[]/L_Mag[] ? GetVariable[ElementNum[],QuadraturePointIndex[]]{$Quench_ratio_EM}/(N_SS[]+1)>=L_QH_B[]/L_Mag[] ? 2: 1 :GetVariable[ElementNum[],QuadraturePointIndex[]]{$Quench_ratio_EM}/(N_SS[]+1)>=L_QH_B[]/L_Mag[] ? 1: 0; // Number of QPF reduction if the front and/or back length is already quenched (QH_EM) [-]
    N_QH_Offset[QH_HT_TH] = GetVariable[ElementNum[],QuadraturePointIndex[]]{$Quench_ratio_TH}/(N_SS[]+1)>=L_QH_F[]/L_Mag[] ? GetVariable[ElementNum[],QuadraturePointIndex[]]{$Quench_ratio_TH}/(N_SS[]+1)>=L_QH_B[]/L_Mag[] ? 2: 1 :GetVariable[ElementNum[],QuadraturePointIndex[]]{$Quench_ratio_TH}/(N_SS[]+1)>=L_QH_B[]/L_Mag[] ? 1: 0; // Number of QPF reduction if the front and/or back length is already quenched (QH_TH) [-]
    N_QPF[Region[{QH_HT_EM,QH_HT_TH}]] = N_SS[]*2-N_QH_Offset[]-N_QH[]; //Number of Normal Zone Propagation Front Origins (QH_HT) [-]
    N_QPF[Region[{noQH_HT_EM,noQH_HT_TH}]]= 2; //Number of Normal Zone Propagation Front Origins (where no QH) [-]
    {% endif %}
    {% if dm.quench_protection.e_cliq.quench_propagation == "2Dx1D" %}
    N_ECLIQ[ECLIQ_HT_EM] = GetVariable[ElementNum[],QuadraturePointIndex[]]{$Quench_ratio_EM}/(N_ECLIQ_units[]+1)>=h_ECLIQ[]/L_Mag[] ? 2*(N_ECLIQ_units[] -1): 0; // Reduction of QPF if the length between ECLIQ units is already quenched (ECLIQ_EM) [-]
    N_ECLIQ[ECLIQ_HT_TH] = GetVariable[ElementNum[],QuadraturePointIndex[]]{$Quench_ratio_TH}/(N_ECLIQ_units[]+1)>=h_ECLIQ[]/L_Mag[] ? 2*(N_ECLIQ_units[] -1): 0; // Reduction of QPF if the length between ECLIQ units is already quenched (ECLIQ_TH) [-]
    L_ECLIQ_F[Region[{ECLIQ_HT_EM,ECLIQ_HT_TH}]] = (L_Mag[]-N_ECLIQ_units[]*L_ECLIQ[])/2-L_ECLIQ_Offset[];  // Front length to magnet end
    L_ECLIQ_B[Region[{ECLIQ_HT_EM,ECLIQ_HT_TH}]] = (L_Mag[]-N_ECLIQ_units[]*L_ECLIQ[])/2+L_ECLIQ_Offset[]; // Back length to magnet end
    N_ECLIQ_Offset[ECLIQ_HT_EM] = GetVariable[ElementNum[],QuadraturePointIndex[]]{$Quench_ratio_EM}/(N_ECLIQ[]+1)>=L_ECLIQ_F[]/L_Mag[] ? GetVariable[ElementNum[],QuadraturePointIndex[]]{$Quench_ratio_EM}/(N_ECLIQ_units[]+1)>=L_ECLIQ_B[]/L_Mag[] ? 2: 1 :GetVariable[ElementNum[],QuadraturePointIndex[]]{$Quench_ratio_EM}/(N_ECLIQ_units[]+1)>=L_ECLIQ_B[]/L_Mag[] ? 1: 0; // Number of QPF reduction if the front and/or back length is already quenched (ECLIQ_EM) [-]
    N_ECLIQ_Offset[ECLIQ_HT_TH] = GetVariable[ElementNum[],QuadraturePointIndex[]]{$Quench_ratio_TH}/(N_ECLIQ[]+1)>=L_ECLIQ_F[]/L_Mag[] ? GetVariable[ElementNum[],QuadraturePointIndex[]]{$Quench_ratio_TH}/(N_ECLIQ_units[]+1)>=L_ECLIQ_B[]/L_Mag[] ? 2: 1 :GetVariable[ElementNum[],QuadraturePointIndex[]]{$Quench_ratio_TH}/(N_ECLIQ_units[]+1)>=L_ECLIQ_B[]/L_Mag[] ? 1: 0; // Number of QPF reduction if the front and/or back length is already quenched (ECLIQ_TH) [-]
    N_QPF[Region[{ECLIQ_HT_EM,ECLIQ_HT_TH}]] = N_ECLIQ_units[]*2-N_ECLIQ_Offset[]-N_ECLIQ[]; //Number of Normal Zone Propagation Front Origins (ECLIQ_HT) [-]
    N_QPF[Region[{noECLIQ_HT_EM,noECLIQ_HT_TH}]]= 2; //Number of Normal Zone Propagation Front Origins (where no ECLIQ) [-]
    {% endif %}
    NZ[]=(N_QPF[]*NZPV[$1,$2,$3]*$DTime*{% if dm.quench_protection.quench_heaters.quench_propagation == "2Dx1D" %}<<dm.quench_protection.quench_heaters.NZPV_multiplier>>{% else %}<<dm.quench_protection.e_cliq.NZPV_multiplier>>{% endif %})/(L_Mag[])  ; // Normal Zone increase per Dt ratio in noECLIQ_zone [-]
    quench_ratio_TH[{% if dm.quench_protection.e_cliq.quench_propagation == "2Dx1D" %}ECLIQ_HT_TH{% else %}QH_HT_TH{% endif %}]   = TestQuench[$1,$2,$3]>0? Min[GetVariable[ElementNum[],QuadraturePointIndex[]]{$Quench_ratio_TH}+L_strip_0[]/(L_Mag[]),1]:0; // Total quench ratio in EM [-]
    quench_ratio_TH[{% if dm.quench_protection.e_cliq.quench_propagation == "2Dx1D" %}noECLIQ_HT_TH{% else %}noQH_HT_TH{% endif %}] = TestQuench[$1,$2,$3]>0? Min[GetVariable[ElementNum[],QuadraturePointIndex[]]{$Quench_ratio_TH},1]:0; // Total quench ratio in TH [-]
    quench_ratio_EM[{% if dm.quench_protection.e_cliq.quench_propagation == "2Dx1D" %}ECLIQ_HT_EM{% else %}QH_HT_EM{% endif %}]   = TestQuench[$1,$2,$3]>0? Min[GetVariable[ElementNum[],QuadraturePointIndex[]]{$Quench_ratio_EM}+L_strip_0[]/(L_Mag[]),1]:0; // Total quench ratio in EM [-]
    quench_ratio_EM[{% if dm.quench_protection.e_cliq.quench_propagation == "2Dx1D" %}noECLIQ_HT_EM{% else %}noQH_HT_EM{% endif %}] = TestQuench[$1,$2,$3]>0? Min[GetVariable[ElementNum[],QuadraturePointIndex[]]{$Quench_ratio_EM},1]:0; // Total quench ratio in EM [-]

{% endif %}    
    // Joule losses of bare part
    // -$1: Temperature [K]
    // -$2: Norm of the magnetic flux density [T]
    // -$3: Current [A]
    jouleLosses[] = CFUN_quenchState_I_Ic[$3,criticalCurrentDensity[$1, $2] * area_fct[]] * rho[$1, $2] * SquNorm[$3/area_fct[]]{% if dm.quench_protection.quench_heaters.quench_propagation == "2Dx1D" %}*quench_ratio_TH[$1,$2,$3]{% endif %};

    
            {% if dm.magnet.geometry.thermal.with_wedges %}
    // Thermal conductivity of the wedges
    // -$1: Temperature [K]
    // -$2: Norm of the magnetic flux density [T]
    kappa[<<nc.omega>><<nc.induced>>_TH] = <<materials[thermalConductivityMacroName[dm.magnet.solve.wedges.material]](RRR=dm.magnet.solve.wedges.RRR)>>;
      
    // heat capacity of wedges
    // -$1: Temperature [K]
    // -$2: Norm of the magnetic flux density [T]
    heatCap[<<nc.omega>><<nc.induced>>_TH] = <<materials[specificHeatCapacityMacroName[dm.magnet.solve.wedges.material]]()>>;
            {% endif %}

     {% for area in areas_to_build['TH'] %}
         {% if area == 'iron_yoke' %}
    // thermal conductivity of the iron yoke TODO: Hardcoded
    kappa[<<nc.omega>><<nc.iron_yoke>>_TH] = 300;
    // heat capacity of iron yoke TODO: Hardcoded
    heatCap[ <<nc.omega>><<nc.iron_yoke>>_TH ] = 50;
        {% else %}
        {% for name in rm_TH[area].vol.names %}
    kappa[<<nc.omega>><<nc[area]>>_TH ] =  <<materials[thermalConductivityMacroName[name]](RRR=dm.magnet.solve.collar.RRR)>>;
    heatCap[ <<nc.omega>><<nc[area]>>_TH ] = <<materials[specificHeatCapacityMacroName[name]]()>>;
        {% endfor %}
        {% endif %}
    {% endfor %}

    
        {% if dm.magnet.solve.collar.transient_effects_enabled %} 
        {% set name = rm_EM['collar'].vol.names[0] %} // debug iron
            {% if 'collar' in areas_to_build['EM'] %} 
    rho[<<nc.omega>><<nc.collar>>_EM] = {% if not name.startswith('BHiron')%} <<materials[resistivityMacroName[name]](RRR=dm.magnet.solve.collar.RRR)>> {% else %} <<materials[resistivityMacroName['SS']](RRR=dm.magnet.solve.collar.RRR)>> {% endif %};
            {% endif %}
            {% if 'collar' in areas_to_build['TH'] %} 
    rho[<<nc.omega>><<nc.collar>>_TH] = {% if not name.startswith('BHiron')%} <<materials[resistivityMacroName[name]](RRR=dm.magnet.solve.collar.RRR)>> {% else %} <<materials[resistivityMacroName['SS']](RRR=dm.magnet.solve.collar.RRR)>>  {% endif %};
            {% endif %}
        {% endif %}
        {% if dm.magnet.solve.poles.transient_effects_enabled %}
        {% set name = rm_EM['poles'].vol.names[0] %} // debug iron
            {% if 'poles' in areas_to_build['EM'] %} 
    rho[<<nc.omega>><<nc.poles>>_EM] = {% if not name.startswith('BHiron')%} <<materials[resistivityMacroName[name]](RRR=dm.magnet.solve.poles.RRR)>> {% else %} <<materials[resistivityMacroName['SS']](RRR=dm.magnet.solve.collar.RRR)>>  {% endif %};
            {% endif %}
            {% if 'poles' in areas_to_build['TH'] %} 
    rho[<<nc.omega>><<nc.poles>>_TH] ={% if not name.startswith('BHiron')%} <<materials[resistivityMacroName[name]](RRR=dm.magnet.solve.poles.RRR)>> {% else %} <<materials[resistivityMacroName['SS']](RRR=dm.magnet.solve.collar.RRR)>>  {% endif %};
            {% endif %}
        {% endif %}
    {% if dm.magnet.mesh.thermal.reference.enabled %}
    // thermal conductivity of the material of the reference mesh.
        {% for name in rm_TH.ref_mesh.vol.names %} 
    kappa[ <<nc.omega>>_refmesh_TH ] = <<materials[thermalConductivityMacroName[name]]()>>; 
    heatCap[ <<nc.omega>>_refmesh_TH ] =  <<materials[specificHeatCapacityMacroName[name]]()>>; 
        {% endfor %}
    {% endif %}   
            {% if dm.magnet.geometry.thermal.use_TSA %}
    For i In {1:num_dirichlet}
        // piece-wise defined const_temp
        const_temp[Region[bnd_dirichlet~{i}]] = val_temperature~{i};
    EndFor

    For n In {1:num_neumann}
        // piece-wise defined heatFlux
        heatFlux[Region[bnd_neumann~{n}]] = val_heatFlux~{n};
    EndFor

    For r In {1:num_robin}
        // piece-wise defined heatExchCoeff
        heatExchCoeff[Region[bnd_robin~{r}]] = val_heatExchCoeff~{r}[$1, $2];
        Tinf[Region[bnd_robin~{r}]] = val_Tinf~{r};
    EndFor

    // TSA material and thickness functions 
    // instead of k and l as arguments, we could add it to the function name increasing the number of functions
                {% set TSAinsulation_layers_number = rm_TH.thin_shells.insulation_types.layers_number + rm_TH.thin_shells.quench_heaters.layers_number + rm_TH.thin_shells.collar.layers_number + rm_TH.thin_shells.poles.layers_number %} //
                {% set TSAinsulation_thicknesses = rm_TH.thin_shells.insulation_types.thicknesses + rm_TH.thin_shells.quench_heaters.thicknesses + rm_TH.thin_shells.collar.thicknesses + rm_TH.thin_shells.poles.thicknesses %} //
                {% set TSAinsulation_thin_shells = rm_TH.thin_shells.insulation_types.thin_shells + rm_TH.thin_shells.quench_heaters.thin_shells + rm_TH.thin_shells.collar.thin_shells + rm_TH.thin_shells.poles.thin_shells %} // 
                {% set TSAinsulation_material = rm_TH.thin_shells.insulation_types.layers_material + rm_TH.thin_shells.quench_heaters.layers_material + rm_TH.thin_shells.collar.layers_material + rm_TH.thin_shells.poles.layers_material %}//

                {% for nr, n_ele in enumerate(TSAinsulation_layers_number) %}
    n_ele_per_tsa_group_<<nr + 1>> = <<n_ele>>;
                    {% for nr_thickness, thickness in enumerate(TSAinsulation_thicknesses[nr]) %}
                        {% for tag in TSAinsulation_thin_shells[nr] %}
                            {% if tag in flip_tags %}
    delta_<<n_ele - nr_thickness - 1>>[Region[<<tag>>]] = <<thickness>>;
    thermalConductivityMass~{<<n_ele - nr_thickness - 1>>}[Region[<<tag>>]] = <<TSA_materials[thermalConductivityTSAMassMacroName[TSAinsulation_material[nr][nr_thickness]]](T_i="$1", T_iPlusOne="$2", thickness_TSA="$3", k="$4", l="$5", GaussianPoints=2)>>;
    thermalConductivityStiffness~{<<n_ele - nr_thickness - 1>>}[Region[<<tag>>]] = <<TSA_materials[thermalConductivityTSAStiffnessMacroName[TSAinsulation_material[nr][nr_thickness]]](T_i="$1", T_iPlusOne="$2", thickness_TSA="$3", k="$4", l="$5", GaussianPoints=2)>>;
    specificHeatCapacity~{<<n_ele - nr_thickness - 1>>}[Region[<<tag>>]] = <<TSA_materials[specificHeatCapacityTSAMacroName[TSAinsulation_material[nr][nr_thickness]]](T_i="$1", T_iPlusOne="$2", thickness_TSA="$3", k="$4", l="$5", GaussianPoints=2)>>;
                            {% else %}
    delta_<<nr_thickness>>[Region[<<tag>>]] = <<thickness>>;
    thermalConductivityMass~{<<nr_thickness>>}[Region[<<tag>>]] = <<TSA_materials[thermalConductivityTSAMassMacroName[TSAinsulation_material[nr][nr_thickness]]](T_i="$1", T_iPlusOne="$2", thickness_TSA="$3", k="$4", l="$5", GaussianPoints=2)>>;
    thermalConductivityStiffness~{<<nr_thickness>>}[Region[<<tag>>]] = <<TSA_materials[thermalConductivityTSAStiffnessMacroName[TSAinsulation_material[nr][nr_thickness]]](T_i="$1", T_iPlusOne="$2", thickness_TSA="$3", k="$4", l="$5", GaussianPoints=2)>>;
    specificHeatCapacity~{<<nr_thickness>>}[Region[<<tag>>]] = <<TSA_materials[specificHeatCapacityTSAMacroName[TSAinsulation_material[nr][nr_thickness]]](T_i="$1", T_iPlusOne="$2", thickness_TSA="$3", k="$4", l="$5", GaussianPoints=2)>>;
                            {% endif %}
                        {% endfor %}
                    {% endfor %}
                {% endfor %}
                {% for nr, n_ele in enumerate(rm_TH.thin_shells.quench_heaters.layers_number) %}
                    {% for nr_thickness, thickness in enumerate(rm_TH.thin_shells.quench_heaters.thicknesses[nr]) %}
                        {% for tag in rm_TH.thin_shells.quench_heaters.thin_shells[nr] %}
                            {% set qh_indexPlusOne = rm_TH.thin_shells.quench_heaters.label[nr][nr_thickness] %}
                            {% if qh_indexPlusOne %}
                                {% set qh_dict = dm.quench_protection.quench_heaters %}
                                {% set qh_index = int(qh_indexPlusOne or 1E20) - 1 %}
                                {% set l_SS = qh_dict.l_stainless_steel[qh_index] / (qh_dict.l_copper[qh_index] + qh_dict.l_stainless_steel[qh_index]) * qh_dict.l[qh_index] %}
                            {% endif %}
                            {% if tag in flip_tags %}
                                {% if qh_indexPlusOne %}
    powerDensity~{<<n_ele - nr_thickness - 1>>}[Region[<<tag>>]] = <<TSA_materials['MATERIAL_QuenchHeater_SSteel_t_T_k'](t_on=qh_dict.t_trigger[qh_index], U_0=qh_dict.U0[qh_index], C=qh_dict.C[qh_index], R_warm=qh_dict.R_warm[qh_index], w_SS=qh_dict.w[qh_index], h_SS=qh_dict.h[qh_index], l_SS=l_SS, mode=1, time="$Time", T_i="$1", T_iPlusOne="$2", thickness_TSA="$3", k="$4", GaussianPoints=2)>>;
                                {% else %}
    powerDensity~{<<n_ele - nr_thickness - 1>>}[Region[<<tag>>]] = 0;
                                {% endif %}
                            {% else %}
                                {% if qh_indexPlusOne %}
    powerDensity~{<<nr_thickness>>}[Region[<<tag>>]] = <<TSA_materials['MATERIAL_QuenchHeater_SSteel_t_T_k'](t_on=qh_dict.t_trigger[qh_index], U_0=qh_dict.U0[qh_index], C=qh_dict.C[qh_index], R_warm=qh_dict.R_warm[qh_index], w_SS=qh_dict.w[qh_index], h_SS=qh_dict.h[qh_index], l_SS=l_SS, mode=1, time="$Time",T_i="$1", T_iPlusOne="$2", thickness_TSA="$3", k="$4", GaussianPoints=2)>>;
                                {% else %}
    powerDensity~{<<nr_thickness>>}[Region[<<tag>>]] = 0;
                                {% endif %}
                            {% endif %}
                        {% endfor %}
                    {% endfor %}
                {% endfor %}
            {% else %}
    // Thermal conductivity of the insulation
    kappa[<<nc.omega>><<nc.insulator>>_TH] = <<materials[thermalConductivityMacroName[list(dm.conductors.values())[0].cable.material_insulation]]()>>;

    // Heat capacity of insulation
    heatCap[ <<nc.omega>><<nc.insulator>>_TH ] = <<materials[specificHeatCapacityMacroName[list(dm.conductors.values())[0].cable.material_insulation]]()>>;
            {% endif %}
        {% endif %}

        {%  if dm.magnet.solve.electromagnetics.solve_type == 'transient' or dm.magnet.solve.thermal.solve_type %}
    // Breakpoints  for the adaptative time stepping scheme (default is the LUT from PS)
            {% if len(dm.magnet.solve.time_stepping.breakpoints)>0 or len(dm.magnet.solve.electromagnetics.time_stepping.breakpoints)>0 or len(dm.magnet.solve.thermal.time_stepping.breakpoints)>0%}
                {% if SIM_MODE == 'Mag_dyn' or SIM_MODE == 'Mag_dyn_0' %}
    Breakpoints= {<<dm.magnet.solve.electromagnetics.time_stepping.breakpoints|join(', ')>>};
                {% elif SIM_MODE == 'Th_Mag_sta'%}
    Breakpoints= {<<dm.magnet.solve.thermal.time_stepping.breakpoints|join(', ')>>};
                {% else %}
    Breakpoints= {<<dm.magnet.solve.time_stepping.breakpoints|join(', ')>>};
                {% endif %}
            {% else %}
    Breakpoints= {<<dm.power_supply.t_control_LUT|join(', ')>>};
            {% endif %}
        {% endif %}
    // Resititivity of the strands accounting for quench propagation
    // -$1: Temperature [K]
    // -$2: Norm of the magnetic flux density [T]
    // -$3: Current [A]
resistivity[<<nc.omega>><<nc.powered>>_EM]= rho[$1, $2] {% if (dm.quench_protection.quench_heaters.quench_propagation == "2Dx1D" or dm.quench_protection.e_cliq.quench_propagation == "2Dx1D" ) and dm.magnet.solve.thermal.solve_type %}*quench_ratio_EM[$1,$2,$3]{% else %}*TestQuench[$1,$2,$3]{% endif %};
{% if dm.magnet.solve.thermal.solve_type %}
resistivity[<<nc.omega>><<nc.powered>>_TH]= rho[$1, $2] {% if (dm.quench_protection.quench_heaters.quench_propagation == "2Dx1D" or dm.quench_protection.e_cliq.quench_propagation == "2Dx1D") and dm.magnet.solve.thermal.solve_type %}*quench_ratio_TH[$1,$2,$3]{% else %}*TestQuench[$1,$2,$3]{% endif %};
{% endif %}

}

    // ------------------- EM CONSTRAINTS -----------------------------------
Constraint {
    // Dirichlet at Boundary of EM domain    
    { Name Dirichlet_a_Mag;
        Case {
          { Region <<nc.boundary>><<nc.omega>> ; Value 0.; }
        }
      }
    {% if dm.circuit.field_circuit %}
      <<cc_macros2.constraints_FCC(dm,rm_EM, flag_active, init_ht, end_ht,CLIQ_dict,ECLIQ_dict, ESC_dict,CC_dict,aux,pol_)>>
    {% endif %}
    {% if not dm.circuit.field_circuit%}
    { Name SourceCurrentDensityZ;
    Case {
        { Region  <<nc.omega>><<nc.powered>>_EM; Type Assign; Value 1; TimeFunction i_fct[];}
        }
        }
    {% endif %}
    {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Mag_dyn' %}
    { Name Init_from_Static;
        Case {
            { Region <<nc.omega>>_EM; Type InitFromResolution; NameOfResolution Static_2_Dynamic ; }
            }
        }
    {% if dm.circuit.field_circuit %}
        { Name Init_from_Static2;
            Case {
                { Region <<nc.omega>>_circuit; Type InitFromResolution; NameOfResolution Static_2_Dynamic ; }
                }
            }
    {% endif %}
    {% endif %}
}

{% if dm.magnet.solve.thermal.solve_type %}
    // ------------------- TH CONSTRAINTS -----------------------------------
Constraint {
    { Name initTemp ;
        Case {
          {% if not dm.magnet.geometry.thermal.use_TSA %}
            {% for nr, _ in enumerate(rm_TH.boundaries.thermal.temperature.bc.names) %}
            { Region <<list(dm.magnet.solve.thermal.overwrite_boundary_conditions.temperature)[nr]>>; Value <<rm_TH.boundaries.thermal.temperature.bc.value[nr]>>;  Type Assign;  } // boundary condition
            {% endfor %}
          {% endif %}
        {% if dm.magnet.geometry.thermal.use_TSA %}
            { Region Region[{allLayers, midLayers {% if dm.magnet.geometry.thermal.use_TSA_new %}, midLayers_col, inner_collar, midLayers_pol, pole_bdry_lines {% endif %}}] ; Value <<dm.magnet.solve.thermal.init_temperature>> ; Type Init; }
        {% endif %}
            { Region <<nc.omega>>_TH ; Value <<dm.magnet.solve.thermal.init_temperature>> ; Type Init; } // init. condition
        }
      }
    {% if dm.magnet.geometry.thermal.use_TSA %}
        {% set lines_tags =  rm_TH.boundaries.thermal.temperature.groups['r1_a1'] +
    rm_TH.boundaries.thermal.temperature.groups['r1_a2'] +
    rm_TH.boundaries.thermal.temperature.groups['r2_a1'] +
    rm_TH.boundaries.thermal.temperature.groups['r2_a2'] +
    rm_TH.boundaries.thermal.cooling.groups['r1_a1'] +
    rm_TH.boundaries.thermal.cooling.groups['r1_a2'] +
    rm_TH.boundaries.thermal.cooling.groups['r2_a1'] +
    rm_TH.boundaries.thermal.cooling.groups['r2_a2'] +
    rm_TH.thin_shells.mid_turns_layers_poles %}

    // split to avoid error for two touching lines in different intDomains
        {% set lines_tags_1 = set(lines_tags).intersection(midLayers_1 + bndDir_1 + bndNeuInt_1_1_1 + bndNeuInt_1_2_1 + bndNeuInt_1_1_2 + bndNeuInt_1_2_2 + bndRobinInt_1_1_1 + bndRobinInt_1_2_1 + bndRobinInt_1_1_2 + bndRobinInt_1_2_2) %}
        {% set lines_tags_2 = set(lines_tags).intersection(midLayers_2 + bndDir_2 + bndNeuInt_2_1_1 + bndNeuInt_2_2_1 + bndNeuInt_2_1_2 + bndNeuInt_2_2_2 + bndRobinInt_2_1_1 + bndRobinInt_2_2_1 + bndRobinInt_2_1_2 + bndRobinInt_2_2_2) %}

    coordList_Python_1_1() = {<<rc.neighbouring_nodes.groups['1_1']|join(', ')>>};
    coordList_Python_2_1() = {<<rc.neighbouring_nodes.groups['2_1']|join(', ')>>};
    coordList_Python_1_2() = {<<rc.neighbouring_nodes.groups['1_2']|join(', ')>>};
    coordList_Python_2_2() = {<<rc.neighbouring_nodes.groups['2_2']|join(', ')>>};
    {% if dm.magnet.geometry.thermal.use_TSA_new %}
    coordList_Python_col_1_1() = {<<rc.neighbouring_nodes.groups['mid2ht_1_1']|join(', ')>>};
    coordList_Python_col_2_1() = {<<rc.neighbouring_nodes.groups['mid2ht_2_1']|join(', ')>>};
    coordList_Python_col_1_2() = {<<rc.neighbouring_nodes.groups['mid2ht_1_2']|join(', ')>>};
    coordList_Python_col_2_2() = {<<rc.neighbouring_nodes.groups['mid2ht_2_2']|join(', ')>>};
    coordList_Python_col() = {<<rc.neighbouring_nodes.groups['mid2col']|join(', ')>>};

    coordList_Python_pol_1_1() = {<<rc.neighbouring_nodes.groups['pole_mid2ht_1_1']|join(', ')>>};
    coordList_Python_pol_2_1() = {<<rc.neighbouring_nodes.groups['pole_mid2ht_2_1']|join(', ')>>};
    coordList_Python_pol_1_2() = {<<rc.neighbouring_nodes.groups['pole_mid2ht_1_2']|join(', ')>>};
    coordList_Python_pol_2_2() = {<<rc.neighbouring_nodes.groups['pole_mid2ht_2_2']|join(', ')>>};
    coordList_Python_mid2pol() = {<<rc.neighbouring_nodes.groups['mid2pol']|join(',')>>};
    {% endif %}
    // apply the mapping
    For i In {1:2}
        For j In {1:2}
          { Name Temperature~{i}~{j} ;
            Case {
                {% if dm.magnet.geometry.thermal.use_TSA_new %}
                // apply TSL mapping at the collar side
                { Region midLayers_col~{i}~{j}; Type Link;
                        RegionRef Bare_Layers~{i}~{j};
                        Coefficient 1;
                    // coordinate list
                    //Function shiftCoordinate[X[], Y[], Z[]]{coordList_Python_col_1()};
                    Function shiftCoordinate[X[], Y[], Z[]]{coordList_Python_col~{i}~{j}()};
                }

                { Region midLayers_pol~{i}~{j}; Type Link;
                        RegionRef Bare_Layers~{i}~{j};
                        Coefficient 1;
                    Function shiftCoordinate[X[], Y[], Z[]]{coordList_Python_pol~{i}~{j}()};
                }
                
                {% endif %}
                // Link DoF of auxiliary shells to actual temperature
              { Region midLayers~{i}~{j} ; Type Link;
                RegionRef Bare_Layers~{i}~{j} ; Coefficient 1;
                // coordList or coordList_Python
                Function shiftCoordinate[X[], Y[], Z[]]{coordList_Python~{i}~{j}()};
              }
            If (num_dirichlet > 0)
                // TODO: proper time dependent boundary conditions
                { Region Region[bndDir~{i}~{j}]; Type Assign;
                  Value const_temp[]; }
            EndIf
            }
          }
        EndFor
    EndFor
    {% if dm.magnet.geometry.thermal.use_TSA_new %}
    { Name Temperature_TSA_sides;
        {% if 'collar' in areas_to_build['TH'] %}
    Case{
        // apply TSL mapping at the collar side
        { Region midLayers_col; Type Link;
                RegionRef Region[{ inner_collar }]; Coefficient 1;
            Function shiftCoordinate[X[], Y[], Z[]]{coordList_Python_col()};// coordinate list
        }}
        {% endif %}
        {% if 'poles' in areas_to_build['TH'] %}
    Case{
        // apply TSL mapping at the pole side
        { Region midLayers_pol; Type Link;
                RegionRef Region[{ pole_bdry_lines }]; Coefficient 1;
            Function shiftCoordinate[X[], Y[], Z[]]{coordList_Python_mid2pol()};// coordinate list
        }}      
            {% endif %} 
    }
    {% endif %}

        {% if dm.magnet.mesh.thermal.isothermal_conductors or dm.magnet.mesh.thermal.isothermal_wedges %}
            { Name isothermal_surs~{1}~{1} ;
            Case {
            {% if dm.magnet.mesh.thermal.isothermal_conductors %}
                {% for tag in rm_TH.powered['r1_a1'].vol.numbers %}
              { Region Region[<<tag>>] ; Type Link;
                RegionRef Region[<<tag>>] ; Coefficient 1;
                Function Vector[<<rc.isothermal_nodes.conductors['1_1'][tag]|join(', ')>>];
                }
                {% endfor %}
            {% endif %}
            {% if dm.magnet.mesh.thermal.isothermal_wedges %}
                {% for tag in rm_TH.induced['r1_a1'].vol.numbers %}
              { Region Region[<<tag>>] ; Type Link;
                RegionRef Region[<<tag>>] ; Coefficient 1;
                Function Vector[<<rc.isothermal_nodes.wedges['1_1'][tag]|join(', ')>>];
                }
                {% endfor %}
            {% endif %}
          }
        }
        { Name isothermal_surs~{2}~{1} ;
          Case {
            {% if dm.magnet.mesh.thermal.isothermal_conductors %}
                {% for tag in rm_TH.powered['r2_a1'].vol.numbers %}
              { Region Region[<<tag>>] ; Type Link;
                RegionRef Region[<<tag>>] ; Coefficient 1;
                Function Vector[<<rc.isothermal_nodes.conductors['2_1'][tag]|join(', ')>>];
                }
                {% endfor %}
            {% endif %}
            {% if dm.magnet.mesh.thermal.isothermal_wedges %}
                {% for tag in rm_TH.induced['r2_a1'].vol.numbers %}
              { Region Region[<<tag>>] ; Type Link;
                RegionRef Region[<<tag>>] ; Coefficient 1;
                Function Vector[<<rc.isothermal_nodes.wedges['2_1'][tag]|join(', ')>>];
                }
                {% endfor %}
            {% endif %}
          }
        }
        { Name isothermal_surs~{1}~{2} ;
          Case {
            {% if dm.magnet.mesh.thermal.isothermal_conductors %}
                {% for tag in rm_TH.powered['r1_a2'].vol.numbers %}
              { Region Region[<<tag>>] ; Type Link;
                RegionRef Region[<<tag>>] ; Coefficient 1;
                Function Vector[<<rc.isothermal_nodes.conductors['1_2'][tag]|join(', ')>>];
                }
                {% endfor %}
            {% endif %}
            {% if dm.magnet.mesh.thermal.isothermal_wedges %}
                {% for tag in rm_TH.induced['r1_a2'].vol.numbers %}
              { Region Region[<<tag>>] ; Type Link;
                RegionRef Region[<<tag>>] ; Coefficient 1;
                Function Vector[<<rc.isothermal_nodes.wedges['1_2'][tag]|join(', ')>>];
                }
                {% endfor %}
            {% endif %}
          }
        }
        { Name isothermal_surs~{2}~{2} ;
          Case {
            {% if dm.magnet.mesh.thermal.isothermal_conductors %}
                {% for tag in rm_TH.powered['r2_a2'].vol.numbers %}
              { Region Region[<<tag>>] ; Type Link;
                RegionRef Region[<<tag>>] ; Coefficient 1;
                Function Vector[<<rc.isothermal_nodes.conductors['2_2'][tag]|join(', ')>>];
                }
                {% endfor %}
            {% endif %}
            {% if dm.magnet.mesh.thermal.isothermal_wedges %}
                {% for tag in rm_TH.induced['r2_a2'].vol.numbers %}
              { Region Region[<<tag>>] ; Type Link;
                RegionRef Region[<<tag>>] ; Coefficient 1;
                Function Vector[<<rc.isothermal_nodes.wedges['2_2'][tag]|join(', ')>>];
                }
                {% endfor %}
            {% endif %}
          }
        }

            {% if dm.magnet.mesh.thermal.isothermal_conductors %}
        { Name isothermal_lines_1 ;
          Case {
                {% for tag in lines_tags_1 %}
              { Region Region[<<tag>>] ; Type Link;
                RegionRef Region[<<tag>>] ; Coefficient 1;
                Function Vector[<<rc.isothermal_nodes.thin_shells[tag]|join(', ')>>];
                }
                {% endfor %}
          }
        }
        { Name isothermal_lines_2 ;
          Case {
                {% for tag in lines_tags_2 %}
              { Region Region[<<tag>>] ; Type Link;
                RegionRef Region[<<tag>>] ; Coefficient 1;
                Function Vector[<<rc.isothermal_nodes.thin_shells[tag]|join(', ')>>];
                }
                {% endfor %}
          }
        }
            {% endif %}
        {% endif %}
    {% endif %}
    }
{% endif %}

FunctionSpace {
    {% if dm.circuit.field_circuit %}
    <<cc_macros2.function_space_FCC(nc,dm,flag_active,SIM_MODE)>>
    {% endif %}

    {%- if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Th_Mag_sta' %}
    { Name H_curl_a_after_projection; Type Form1P;
        BasisFunction {
          { Name se_after_projection; NameOfCoef ae_after_projection; Function BF_PerpendicularEdge;
            Support Region[{<<nc.omega>>_TH, allLayers, outer_collar}] ; Entity NodesOf[ All ]; }
        }
      }    
    {% endif %}
    {% if USE_THERMAL_PROJECTION or dm.quench_protection.quench_heaters.quench_propagation == "2Dx1D" or dm.quench_protection.e_cliq.quench_propagation == "2Dx1D"%}
    { Name Hgrad_T_artificial_dof; Type Scalar;  
        BasisFunction {
            { Name T_artificial; NameOfCoef T_artificial; Function BF_Node;
        Support Region[{{%if 'collar' in areas_to_build['EM']%}<<nc.omega>><<nc.collar>>_EM {% endif %}<<nc.omega>><<nc.powered>>_EM}] ; Entity NodesOf[ All ]; }
        }
    }    
    {% endif %}

    { Name Hcurl_a_Mag_2D; Type Form1P; // Magnetic vector potential a
      BasisFunction {
        { Name se; NameOfCoef ae; Function BF_PerpendicularEdge;
          Support Region[{<<nc.omega>>_EM{%- if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Th_Mag_sta' %}, allLayers, outer_collar{% endif %}}] ; Entity NodesOf[ All ]; }
      }
      Constraint {
        { NameOfCoef ae; EntityType NodesOf;
            NameOfConstraint Dirichlet_a_Mag; }
        {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Mag_dyn' %}
        { NameOfCoef ae; EntityType NodesOf;
        NameOfConstraint Init_from_Static; }
        {% endif %}
      }
    }
    { Name Hregion_j_Mag_2D; Type Vector; // Electric current density js
      BasisFunction {
        { Name sr; NameOfCoef jsr; Function BF_RegionZ;
          Support <<nc.omega>><<nc.powered>>_EM; Entity <<nc.omega>><<nc.powered>>_EM; }
      }
      {% if dm.circuit.field_circuit %}
      GlobalQuantity {
        { Name I_mag; Type AliasOf;        NameOfCoef jsr; }
        { Name U_mag; Type AssociatedWith; NameOfCoef jsr; }
      }
        {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Mag_dyn' %}
        Constraint {
            { NameOfCoef I_mag; EntityType Region;
              NameOfConstraint Init_from_Static; }
              { NameOfCoef U_mag; EntityType Region;
                  NameOfConstraint Init_from_Static; }
              }
        {% endif %}
      
      {% else %}
      Constraint {
        { NameOfCoef jsr; EntityType Region;
          NameOfConstraint SourceCurrentDensityZ; }
      }
      {% endif %}
    }


{% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Th_Mag_sta' %}
{ Name H_curl_a_artificial_dof; Type Form1P;  
    BasisFunction {
        { Name se_after_projection; NameOfCoef ae_after_projection; Function BF_PerpendicularEdge;
        Support <<nc.omega>>_TH ; Entity NodesOf[ All ]; }
    }
    Constraint {
    }
    }

{ Name Hgrad_T; Type Form0;
    BasisFunction {
      { Name un;  NameOfCoef ui;  Function BF_Node;
        {% if dm.magnet.geometry.thermal.use_TSA and not dm.magnet.geometry.thermal.use_TSA_new%}
          Support Region[ {<<nc.omega>>_TH {% if dm.magnet.solve.thermal.collar_cooling.enabled %}, bndCollarGaps {% endif %} } ]; 
          Entity NodesOf[All, Not allLayers];
        {% elif dm.magnet.geometry.thermal.use_TSA_new %}
          Support Region[ {<<nc.omega>>_TH {% if dm.magnet.solve.thermal.collar_cooling.enabled %}, bndCollarGaps {% endif %} } ]; 
          Entity NodesOf[All, Not {allLayers, inner_collar {% if 'poles' in areas_to_build['TH']%}, pole_bdry_lines {% endif %}} ];
        {% else %}
          Support Region[{<<nc.omega>>_TH, Bnds_support}] ; Entity NodesOf[All];
        {% endif %}
      }

    {% if dm.magnet.geometry.thermal.use_TSA %}
      // temperature on shells following checkered support idea as indicated
      // by two indices
      // FYI: another possibility would be to treat the extremity points of
      // the shells separately
      For i In {1:2}
        For j In {1:2}
          { Name udn~{i}~{j}; NameOfCoef udi~{i}~{j}; Function BF_Node;
            Support Region[{midLayers~{i}~{j}, Domain_Insulated_Str~{i}~{j} {% if dm.magnet.geometry.thermal.use_TSA_new %}, midLayers_col~{i}~{j}, midLayers_pol~{i}~{j} {% endif %}}];
            Entity NodesOf[{midLayers~{i}~{j}, Bare_Layers~{i}~{j} {% if dm.magnet.geometry.thermal.use_TSA_new %}, midLayers_col~{i}~{j}, midLayers_pol~{i}~{j} {% endif %}}]; }
        EndFor
      EndFor
    {% endif %}
    {% if dm.magnet.geometry.thermal.use_TSA_new %}
        { Name udn_TSA_not_ht_side; NameOfCoef udi_TSA_not_ht; Function BF_Node;
          Support Region[{midLayers_col, inner_collar, <<nc.omega>><<nc.collar>>_TH {% if 'poles' in areas_to_build['TH'] %}, midLayers_pol, pole_bdry_lines, <<nc.omega>><<nc.poles>>_TH {% endif %}}]; // poles needed here for the one point disconnection, REMOVED FOR NOW: % if 'poles' in areas_to_build['TH'] %, <<nc.omega>><<nc.poles>>_TH % endif %
          Entity NodesOf[{midLayers_col, inner_collar {% if 'poles' in areas_to_build['TH'] %}, midLayers_pol, pole_bdry_lines {% endif %}}]; }
    {% endif %}
    }

  {% if dm.magnet.geometry.thermal.use_TSA %}
    SubSpace {
      // "vertical" subspaces, up and down are connected via thin shell
      { Name Shell_Up_1;   NameOfBasisFunction {udn_1_1, udn_1_2};}
      { Name Shell_Down_1; NameOfBasisFunction {udn_2_2, udn_2_1};}

      // "horizontal" subspaces, up and down are connected via thin shell
      { Name Shell_Up_2;   NameOfBasisFunction {udn_1_1, udn_2_1}; }
      { Name Shell_Down_2; NameOfBasisFunction {udn_2_2, udn_1_2}; }
    
    {% if dm.magnet.geometry.thermal.use_TSA_new %}
    // add up and down for the new layer
      { Name Shell_Up_collar_1;  NameOfBasisFunction {}; }
      { Name Shell_Down_collar_1;  NameOfBasisFunction {};}
      { Name Shell_Up_collar_2;  NameOfBasisFunction {udn_1_2, udn_2_2, udn_1_1, udn_2_1 }; }
      { Name Shell_Down_collar_2;  NameOfBasisFunction {udn_TSA_not_ht_side};} 
      {% if 'poles' in areas_to_build['TH'] %}
      { Name Shell_Up_pole_1;  NameOfBasisFunction {udn_1_2, udn_2_2, udn_1_1, udn_2_1 }; }
      { Name Shell_Down_pole_1;  NameOfBasisFunction {udn_TSA_not_ht_side};}
      { Name Shell_Up_pole_2;  NameOfBasisFunction {udn_1_2, udn_2_2, udn_1_1, udn_2_1 }; } // technically only two are needed here (not all four)
      { Name Shell_Down_pole_2;  NameOfBasisFunction {udn_TSA_not_ht_side};}
      {% endif %}
    {% endif %}
    }
  {% endif %}

    Constraint {
    {% if dm.magnet.geometry.thermal.use_TSA %}
      For i In {1:2} // includes halfturns and shell lines
        For j In {1:2}
          { NameOfCoef udi~{i}~{j};  EntityType NodesOf;
            NameOfConstraint Temperature~{i}~{j}; }
          {% if dm.magnet.mesh.thermal.isothermal_conductors %}
            {NameOfCoef udi~{i}~{j};  EntityType NodesOf;
            NameOfConstraint isothermal_surs~{i}~{j}; }
          {% endif %}
          { NameOfCoef udi~{i}~{j};  EntityType NodesOf;
            NameOfConstraint initTemp; }
        EndFor
      EndFor
    {% endif %}
        {% if dm.magnet.geometry.thermal.use_TSA_new %} // apply link + initial temperature on the collar+pole boundary lines
          { NameOfCoef udi_TSA_not_ht; EntityType NodesOf; NameOfConstraint Temperature_TSA_sides; }
          { NameOfCoef udi_TSA_not_ht;  EntityType NodesOf; NameOfConstraint initTemp; }
        {% endif %}
          {NameOfCoef ui; EntityType NodesOf; NameOfConstraint initTemp; } // do not constraint second order basis function as it's already covered by ui
    }
  }

    {% if dm.magnet.geometry.thermal.use_TSA %}
// virtual thermal shell layers
For tsaGroup In {1: <<len(TSAinsulation_layers_number)>>}
      For i In {1:n_ele_per_tsa_group~{tsaGroup}-1}
        For j In {1:2} // horizontal vs vertical
          { Name Hgrad_T~{i}~{j}~{tsaGroup}; Type Form0 ;
            BasisFunction {
              { Name sn~{i}~{j}~{tsaGroup}; NameOfCoef Tn~{i}~{j}~{tsaGroup} ; Function BF_Node ;
                Support intDomain~{j}~{tsaGroup} ; Entity NodesOf[ All ] ; } 
            }
            Constraint {
        {% if dm.magnet.mesh.thermal.isothermal_conductors %}
              { NameOfCoef Tn~{i}~{j}~{tsaGroup};  EntityType NodesOf;
                NameOfConstraint isothermal_lines~{j}; }
        {% endif %}
              { NameOfCoef Tn~{i}~{j}~{tsaGroup};  EntityType NodesOf;
                NameOfConstraint initTemp; }
            }
          }
        EndFor
      EndFor
    EndFor
{% endif %}
{% endif %}
}


Jacobian {
    { Name Jac_Vol_EM ;
        Case {
          { Region <<nc.omega>><<nc.air_far_field>>_EM ;
            Jacobian VolSphShell {<<rm_EM.air_far_field.vol.radius_in>>, <<rm_EM.air_far_field.vol.radius_out>>} ; }
          { Region All ; Jacobian Vol ; }
        }
      }
    {% if dm.magnet.solve.thermal.solve_type %}
    { Name Jac_Vol_TH ;
        Case {
          { Region All ; Jacobian Vol ; }
        }
    }
    { Name Jac_Sur_TH ;
        Case {
          { Region All ; Jacobian Sur ; }
        }
    }
    {% endif %}
}

Integration {
    { Name Int_EM ;
        Case {
          { Type Gauss ;
            Case {
              { GeoElement Point ; NumberOfPoints 1 ; }
              { GeoElement Line ; NumberOfPoints 2 ; }
              { GeoElement Triangle ; NumberOfPoints 3 ; }
              { GeoElement Quadrangle ; NumberOfPoints 4 ; }
            }
          }
        }
    }

    {% if dm.magnet.solve.thermal.solve_type %}
    { Name Int_line_TH ;
    Case {
      { Type Gauss ;
        Case {
          { GeoElement Line ; NumberOfPoints 2 ; }
        }
      }
    }
    }
    
    { Name Int_TH ;
    Case {
      { Type Gauss ;
        Case {
          { GeoElement Triangle ; NumberOfPoints 3 ; }
          { GeoElement Quadrangle ; NumberOfPoints 4 ; }
        }
      }
    }
    }
    {% endif %}
}

Formulation {
    {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Mag_dyn' or SIM_MODE == 'Mag_sta' or SIM_MODE == 'Th_Mag_sta' %}
    { Name Magnetostatics_a_2D; Type FemEquation;
        Quantity {
            { Name a ; Type Local; NameOfSpace Hcurl_a_Mag_2D; }
            { Name is; Type Local; NameOfSpace Hregion_j_Mag_2D; }
        {% if dm.circuit.field_circuit %}
            { Name I_mag; Type Global; NameOfSpace Hregion_j_Mag_2D[I_mag]; }
            { Name U_mag; Type Global; NameOfSpace Hregion_j_Mag_2D[U_mag]; }
            { Name Iz; Type Global; NameOfSpace CircuitSpace[Iz]; }
            { Name Uz; Type Global; NameOfSpace CircuitSpace[Uz]; }
        {% endif %}
        }
        Equation {
            Integral { [ nu[{d a}] * Dof{d a} , {d a} ];
            In <<nc.omega>>_EM; Jacobian Jac_Vol_EM; Integration Int_EM; }
    
        {% if 'iron_yoke' in areas_to_build['EM'] %}
            Integral { JacNL[ dnu_db[{d a}] * Dof{d a} , {d a} ];
            In <<nc.omega>><<nc.iron_yoke>>_EM; Jacobian Jac_Vol_EM; Integration Int_EM; } 
        {% endif %}
            Integral { [ -Dof{is}{% if not dm.circuit.field_circuit %}*sign_fct[]{% endif %}/area_fct[], {a} ];
            In <<nc.omega>><<nc.powered>>_EM; Jacobian Jac_Vol_EM; Integration Int_EM; }
             {% if SIM_MODE == 'Mag_dyn' or SIM_MODE == 'Mag_dyn_0' or SIM_MODE == 'Mag_sta' %}
            Integral { [ resistivity[<<dm.magnet.solve.electromagnetics.time_stepping.T_sim>>,Norm[{d a}],Abs[CompZ[{is}]]]* Dof{is} , {is} ];  // Resistive Term
            {% else %}
            Integral { [resistivity[T_EM_fct[],Norm[{d a}],Abs[CompZ[{is}]]]* Dof{is} , {is} ];  // Resistive Term
            {% endif %}
            In <<nc.omega>><<nc.powered>>_EM; Jacobian Jac_Vol_EM; Integration Int_EM; }

        {% if dm.circuit.field_circuit %}
            GlobalTerm {[-Dof{U_mag} , {I_mag}] ; In Omega_p_EM_r ; }
            GlobalTerm {[Dof{U_mag}  , {I_mag}] ; In Omega_p_EM_l ; }
            // U = L dI/dt in inductive elements
            {%  if flag_active['L']==1 %}
            GlobalTerm {DtDof[L[] * Dof{Iz}, {Iz}] ; In Omega_inductance ; }
            GlobalTerm {[  -Dof{Uz}         ,  {Iz}] ; In Omega_inductance; }
            {%  endif %}

            // U = R I in resistive elements
            {%  if flag_active['R']==1 %}
            GlobalTerm {NeverDt[R[] * Dof{Iz}, {Iz}] ; In Omega_resistance ; }
            GlobalTerm {NeverDt[-Dof{Uz}     , {Iz}] ; In Omega_resistance ; }
            {%  endif %}

            // Switch
            {%  if flag_active['SW']==1 %}
                GlobalTerm {NeverDt[ Coef_switch[]*Dof{Uz}/R[], {Iz}] ; In Omega_switch ; }
                GlobalTerm {NeverDt[-Dof{Iz}     , {Iz}] ; In Omega_switch ; }
            {%  endif %}

            // U = R(I) I in varistor elements
            {%  if flag_active['V']==1 %}
            GlobalTerm {NeverDt[R[{Iz}]*Dof{Iz}, {Iz}] ; In Omega_varistor ; }
            GlobalTerm {NeverDt[-Dof{Uz}       , {Iz}] ; In Omega_varistor ; }
            {%  endif %}

            // U = R(I) I in diode elements
            {%  if flag_active['D']==1 %}
            GlobalTerm { NeverDt[ R[{Iz}] * Dof{Iz} , {Iz} ]; In Omega_diode; }
            GlobalTerm { NeverDt[ -Dof{Uz}          , {Iz} ]; In Omega_diode; }
            {%  endif %}

            // U = R(I) I in thyristor elements (Same as diode but with switch)
            {%  if flag_active['Th']==1 %}
            GlobalTerm { NeverDt[ R[{Iz}] * Dof{Iz} , {Iz} ]; In Omega_thyristor; }
            GlobalTerm { NeverDt[ -Dof{Uz}          , {Iz} ]; In Omega_thyristor; }
            {%  endif %}

            // I = C dU/dt Capacitive elements
            {%  if flag_active['C']==1 %}
            GlobalTerm{ DtDof[ C[] * Dof{Uz}, {Iz} ]; In Omega_capacitance; }
            GlobalTerm{ NeverDt[ -Dof{Iz}   , {Iz} ]; In Omega_capacitance; }
            {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Mag_dyn' or SIM_MODE == 'Th_Mag_sta' or SIM_MODE == 'Mag_sta'%}
            {% if flag_active["CLIQ"] %}
            GlobalTerm{ [ <<dm.quench_protection.cliq.U0>>, {Iz} ]; In Omega_CLIQ_C; }
            GlobalTerm{ [ -Dof{Uz}   , {Iz} ]; In Omega_CLIQ_C; }
            {% endif %}
            {% if flag_active["ESC"] %}
            {%for i in range(ESC_dict["Units"])%}
            GlobalTerm{ [ <<dm.quench_protection.esc.U0[i]>>, {Iz} ]; In Region[{<<'Omega_ESC_C1_'~(i+1)>>,<<'Omega_ESC_C2_'~(i+1)>>}]; }
            GlobalTerm{ [ -Dof{Uz}   , {Iz} ]; In Region[{<<'Omega_ESC_C1_'~(i+1)>>,<<'Omega_ESC_C2_'~(i+1)>>}]; }

            {% endfor %}
            {% endif %}
            {% endif %}
            {%  endif %}

            GlobalTerm { [0 * Dof{Uz} , {Iz}] ; In Omega_circuit; }
            GlobalTerm { [0 * Dof{Iz} , {Iz}] ; In Omega_circuit; }
            GlobalEquation{
                Type Network; NameOfConstraint ElectricalCircuit;
                { Node {I_mag}; Loop {U_mag}; Equation {U_mag}; In <<nc.omega>><<nc.powered>>_EM; }
                { Node {Iz}; Loop {Uz}; Equation {Uz}; In Omega_circuit; }
            }
        {% endif %}
        }
    }
    {% endif %}
    {% if SIM_MODE != 'Mag_sta' and SIM_MODE != 'Th_Mag_sta' %}
    { Name Magnetodynamics_a_2D; Type FemEquation;
        Quantity {
            { Name a ; Type Local; NameOfSpace Hcurl_a_Mag_2D; }
            { Name is; Type Local; NameOfSpace Hregion_j_Mag_2D; }
        {% if dm.circuit.field_circuit %}
            { Name I_mag; Type Global; NameOfSpace Hregion_j_Mag_2D[I_mag]; }
            { Name U_mag; Type Global; NameOfSpace Hregion_j_Mag_2D[U_mag]; }
            { Name Iz; Type Global; NameOfSpace CircuitSpace[Iz]; }
            { Name Uz; Type Global; NameOfSpace CircuitSpace[Uz]; }
        {% endif %}
        }
        Equation {
            Integral { [ nu[{d a}] * Dof{d a} , {d a} ];
                In <<nc.omega>>_EM; Jacobian Jac_Vol_EM; Integration Int_EM; }
    
        {% if 'iron_yoke' in areas_to_build['EM'] %}
            Integral { JacNL[ dnu_db[{d a}] * Dof{d a} , {d a} ]; 
                In <<nc.omega>><<nc.iron_yoke>>_EM; Jacobian Jac_Vol_EM; Integration Int_EM; }
        {% endif %}
            Integral { [ -Dof{is}{% if not dm.circuit.field_circuit %}*sign_fct[]{% endif %}/area_fct[], {a} ];
                In <<nc.omega>><<nc.powered>>_EM; Jacobian Jac_Vol_EM; Integration Int_EM; }
            {% if SIM_MODE == 'Mag_dyn' or SIM_MODE == 'Mag_dyn_0' %}
            Integral { [ resistivity[<<dm.magnet.solve.electromagnetics.time_stepping.T_sim>>,Norm[{d a}],Abs[CompZ[{is}]]]* Dof{is} , {is} ];  // Resistive Term
            {% else %}
        Integral { [resistivity[T_EM_fct[],Norm[{d a}],Abs[CompZ[{is}]]]* Dof{is} , {is} ];  // Resistive Term
            {% endif %}
                In <<nc.omega>><<nc.powered>>_EM; Jacobian Jac_Vol_EM; Integration Int_EM; }
        /*
        // @emma: removed voltage response of cable
        // final formulation:
        // DISCC --> inter-strand coupling effects, ROHM -> Strand-level respose to applied field, ROHF --> Strand-level response to transport current
        // --> P in W/m^3, M in A/m, U in V
        */
        {% if 'collar' in areas_to_build['EM'] and dm.magnet.solve.collar.transient_effects_enabled %}
            {% if USE_THERMAL_PROJECTION %}
        Integral { DtDof [ 1.0/rho[GetVariable[ElementNum[], QuadraturePointIndex[]]{$T_a_collar}]*Dof{a} , {a} ];  // inductive response of eddy currents in the collar
                In <<nc.omega>><<nc.collar>>_EM; Jacobian Jac_Vol_EM; Integration Int_EM; }       
            {% else %}
        Integral { DtDof [ 1.0/rho[<<dm.magnet.solve.thermal.init_temperature>>]*Dof{a} , {a} ];  // inductive response of eddy currents in the collar
                In <<nc.omega>><<nc.collar>>_EM; Jacobian Jac_Vol_EM; Integration Int_EM; }       
            {% endif %} 
        {% endif %} 
        {% if 'poles' in areas_to_build['EM'] and dm.magnet.solve.poles.transient_effects_enabled %}
        Integral { DtDof [ 1.0/rho[<<dm.magnet.solve.thermal.init_temperature>>]*Dof{a} , {a} ];  // inductive response of eddy currents in the poles
                In <<nc.omega>><<nc.poles>>_EM; Jacobian Jac_Vol_EM; Integration Int_EM; }    
        {% endif %}

        {% if dm.magnet.geometry.thermal.with_wedges and dm.magnet.solve.wedges.transient_effects_enabled %}
        Integral { DtDof [ 1.0/rho[T_EM_fct[], Norm[{d a}]]*Dof{a} , {a} ];  // inductive response of eddy currents in the wedges
                In Region [{<<nc.omega>><<nc.induced>>_EM}]; Jacobian Jac_Vol_EM; Integration Int_EM; }
        {% endif %}
        /*
        // DEBUG: init_temperature is to be replaced with the temperature T, but for this we need a projection TH -> EM. This is not possible in the collar region due to an interpolation error in getdp.
        // 1. we could use the average temperature as an approximation -> see USE_THERMAL_PROJECTION
        // 2. we could assume the temperature doesn't change much so we can use the initial temperature (no projection)
        */

        {% if dm.circuit.field_circuit %}

        GlobalTerm {[-Dof{U_mag} , {I_mag}] ; In Omega_p_EM_r ; }
        GlobalTerm {[Dof{U_mag}  , {I_mag}] ; In Omega_p_EM_l ; }

                // U = L dI/dt in inductive elements
            {%  if flag_active['L']==1 %}
                GlobalTerm {DtDof[L[] * Dof{Iz}, {Iz}] ; In Omega_inductance ; }
                GlobalTerm {[  -Dof{Uz}         ,  {Iz}] ; In Omega_inductance; }
            {%  endif %}

                // U = R I in resistive elements
            {%  if flag_active['R']==1 %}
                GlobalTerm {NeverDt[R[] * Dof{Iz}, {Iz}] ; In Omega_resistance ; }
                GlobalTerm {NeverDt[-Dof{Uz}     , {Iz}] ; In Omega_resistance ; }
            {%  endif %}

            // Switch
            {%  if flag_active['SW']==1 %}
            GlobalTerm {NeverDt[ Coef_switch[]*Dof{Uz}/R[], {Iz}] ; In Omega_switch ; }
            GlobalTerm {NeverDt[-Dof{Iz}     , {Iz}] ; In Omega_switch ; }
            {%  endif %}

                // U = R(I) I in varistor elements
            {%  if flag_active['V']==1 %}
                GlobalTerm {NeverDt[R[{Iz}]*Dof{Iz}, {Iz}] ; In Omega_varistor ; }
                GlobalTerm {NeverDt[-Dof{Uz}       , {Iz}] ; In Omega_varistor ; }
            {%  endif %}
                
                // U = R(I) I in diode elements
            {%  if flag_active['D']==1 %}
                GlobalTerm { NeverDt[ R[{Iz}] * Dof{Iz} , {Iz} ]; In Omega_diode; }
                GlobalTerm { NeverDt[ -Dof{Uz}          , {Iz} ]; In Omega_diode; }
            {%  endif %}

                // U = R(I) I in thyristor elements (Same as diode but with switch)
            {%  if flag_active['Th']==1 %}
                GlobalTerm { NeverDt[ R[{Iz}] * Dof{Iz} , {Iz} ]; In Omega_thyristor; }
                GlobalTerm { NeverDt[ -Dof{Uz}          , {Iz} ]; In Omega_thyristor; }
            {%  endif %}

                // I = C dU/dt Capacitive elements
            {%  if flag_active['C']==1 %}
                GlobalTerm{ DtDof[ C[] * Dof{Uz}, {Iz} ]; In Omega_capacitance; }
                GlobalTerm{ NeverDt[ -Dof{Iz}   , {Iz} ]; In Omega_capacitance; }
            {%  endif %}

                GlobalTerm { [0 * Dof{Uz} , {Iz}] ; In Omega_circuit; }
                GlobalTerm { [0 * Dof{Iz} , {Iz}] ; In Omega_circuit; }
                GlobalEquation{
                    Type Network; NameOfConstraint ElectricalCircuit;
                    { Node {I_mag}; Loop {U_mag}; Equation {U_mag}; In <<nc.omega>><<nc.powered>>_EM; }
                    { Node {Iz}; Loop {Uz}; Equation {Uz}; In Omega_circuit; }
                    }       
                
            
        {% endif %}
        }
    }
    {% endif %}

    {% if dm.magnet.solve.thermal.solve_type %}
    // Dummy formulation just to save the values of the norm of B from the EM mesh on the Gaussian points of
    // the thermal mesh. Alternatively, a Galerkin projection could be used.
    { Name Projection_EM_to_TH; Type FemEquation;
        Quantity {
            {Name a_before_projection; Type Local; NameOfSpace Hcurl_a_Mag_2D; }
            {Name a_after_projection; Type Local; NameOfSpace H_curl_a_after_projection; }
        }
        Equation {
        // HT + Wedge + collar/poles etc
        Integral { [ - SetVariable[{d a_before_projection}, ElementNum[], QuadraturePointIndex[]]{$b_before_projection}, {d a_after_projection} ];
            In <<nc.omega>>_noninsulation_areas_TH; Integration Int_TH; Jacobian Jac_Vol_TH; }
        Integral { [ Dof{d a_after_projection}, {d a_after_projection} ];
            In <<nc.omega>>_noninsulation_areas_TH; Integration Int_TH; Jacobian Jac_Vol_TH; }

        Integral { [ - {a_before_projection}, {a_after_projection} ];
            In Region[{allLayers, outer_collar}]; Integration Int_line_TH; Jacobian Jac_Sur_TH; }
            
        Integral { [ Dof{a_after_projection}, {a_after_projection} ];
            In Region[{allLayers, outer_collar}]; Integration Int_line_TH; Jacobian Jac_Sur_TH; }
            }
        }             
        {% if USE_THERMAL_PROJECTION %}
    { Name Projection_TH_to_EM; Type FemEquation;
        Quantity {
            { Name T; Type Local; NameOfSpace Hgrad_T; }
            { Name T_artificial_dof; Type Local; NameOfSpace Hgrad_T_artificial_dof; }
        }
        Equation {
            Integral { [ - SetVariable[$T_a_col, ElementNum[], QuadraturePointIndex[]]{$T_a_collar}, {T_artificial_dof} ]; 
                In <<nc.omega>><<nc.collar>>_EM; Integration Int_EM; Jacobian Jac_Vol_EM; }  
            Integral { [ Dof{T_artificial_dof}, {T_artificial_dof} ];
                In <<nc.omega>><<nc.collar>>_EM; Integration Int_EM; Jacobian Jac_Vol_EM; }
            }
        }     
        {% endif %}
        {% if dm.quench_protection.quench_heaters.quench_propagation == "2Dx1D" or dm.quench_protection.e_cliq.quench_propagation == "2Dx1D" %}
        { Name Quench_Prop_TH; Type FemEquation;
        Quantity {
            {Name a_before_projection; Type Local; NameOfSpace Hcurl_a_Mag_2D; }
            {Name a_artificial_dof; Type Local; NameOfSpace H_curl_a_artificial_dof; }
            {Name T; Type Local; NameOfSpace Hgrad_T; }
        }
        Equation {
            
        Integral { [ - SetVariable[GetVariable[ElementNum[], QuadraturePointIndex[]]{$Quench_ratio_TH} + NZ[{T},0,I2TH_fct[]] , ElementNum[], QuadraturePointIndex[]]{$Quench_ratio_TH}, {d a_artificial_dof} ];
            In <<nc.omega>><<nc.powered>>_TH; Integration Int_TH; Jacobian Jac_Vol_TH; }
        Integral { [ Dof{a_artificial_dof}, {a_artificial_dof} ];
            In <<nc.omega>><<nc.powered>>_TH; Integration Int_TH; Jacobian Jac_Vol_TH; }
        }
    }
    { Name Quench_Prop_EM; Type FemEquation;
        Quantity {
            {Name T_artificial_dof; Type Local; NameOfSpace Hgrad_T_artificial_dof; }
            {Name a; Type Local; NameOfSpace Hcurl_a_Mag_2D; }
            { Name is; Type Local; NameOfSpace Hregion_j_Mag_2D; }
        }
        Equation {
        Integral { [ - SetVariable[ GetVariable[ElementNum[], QuadraturePointIndex[]]{$Quench_ratio_EM} + NZ[T_EM_fct[],Norm[{d a}],Abs[CompZ[{is}]]] , ElementNum[], QuadraturePointIndex[]]{$Quench_ratio_EM}, {d T_artificial_dof} ];
            In <<nc.omega>><<nc.powered>>_EM; Integration Int_EM; Jacobian Jac_Vol_EM; }

        Integral { [ Dof{T_artificial_dof}, {T_artificial_dof} ];
            In <<nc.omega>><<nc.powered>>_EM; Integration Int_EM; Jacobian Jac_Vol_EM; }
        }
    }
        {% endif %}    
    {% endif %}           

    {% if dm.magnet.solve.thermal.solve_type %}
    { Name Thermal_T;   Type FemEquation;
        Quantity {
      // cont temperature
      { Name T; Type Local; NameOfSpace Hgrad_T; }
        {% if dm.magnet.geometry.thermal.use_TSA %}
        For j In {1:2} // "vertical" and "horizontal" separated
            For tsaGroup In {1:<<len(TSAinsulation_layers_number)>>}
                If (tsaGroup < <<len(rm_TH.thin_shells.insulation_types.layers_number + rm_TH.thin_shells.quench_heaters.layers_number)+1>>) 
                    // TSA + QH
              { Name Ti~{0}~{j}~{tsaGroup}; Type Local;
                        NameOfSpace Hgrad_T[Shell_Up~{j}]; }                     // outer temp up
                    For i In {1:n_ele_per_tsa_group~{tsaGroup}-1}
                        { Name Ti~{i}~{j}~{tsaGroup} ; Type Local ;
                            NameOfSpace Hgrad_T~{i}~{j}~{tsaGroup}; }            // auxiliary shells in between
                    EndFor
                    { Name Ti~{n_ele_per_tsa_group~{tsaGroup}}~{j}~{tsaGroup}; Type Local;
                        NameOfSpace Hgrad_T[Shell_Down~{j}]; }                   //outer temp down
                ElseIf (tsaGroup < <<len(rm_TH.thin_shells.insulation_types.layers_number + rm_TH.thin_shells.quench_heaters.layers_number + rm_TH.thin_shells.collar.layers_number )+1>>) 
                    // collar
                    { Name Ti~{0}~{j}~{tsaGroup}; Type Local;
                        NameOfSpace Hgrad_T[Shell_Up_collar~{j}]; } 
                For i In {1:n_ele_per_tsa_group~{tsaGroup}-1}
                    { Name Ti~{i}~{j}~{tsaGroup} ; Type Local ;
                      NameOfSpace Hgrad_T~{i}~{j}~{tsaGroup}; }
                EndFor
              { Name Ti~{n_ele_per_tsa_group~{tsaGroup}}~{j}~{tsaGroup}; Type Local;
                        NameOfSpace Hgrad_T[Shell_Down_collar~{j}]; } 
                Else 
                    // pole thin shell lines
                    { Name Ti~{0}~{j}~{tsaGroup}; Type Local;
                        NameOfSpace Hgrad_T[Shell_Up_pole~{j}]; } 
                    For i In {1:n_ele_per_tsa_group~{tsaGroup}-1}
                        { Name Ti~{i}~{j}~{tsaGroup} ; Type Local ;
                            NameOfSpace Hgrad_T~{i}~{j}~{tsaGroup}; }
                    EndFor
                    { Name Ti~{n_ele_per_tsa_group~{tsaGroup}}~{j}~{tsaGroup}; Type Local;
                        NameOfSpace Hgrad_T[Shell_Down_pole~{j}]; } 
                EndIf
          EndFor
        EndFor
        {% endif %}
      { Name a_after_projection; Type Local; NameOfSpace H_curl_a_after_projection; }
        }
        Equation {
            Integral { [ kappa[{T}, Norm[{d a_after_projection}]] * Dof{d T} , {d T} ] ;
                In Region[ {<<nc.omega>>_TH } ]; Integration Int_TH ; Jacobian Jac_Vol_TH ; }
            
            Integral { DtDof[ heatCap[{T}, Norm[{d a_after_projection}]] * Dof{T}, {T} ];
                In Region[ {<<nc.omega>>_TH } ]; Integration Int_TH; Jacobian Jac_Vol_TH;  }
       
        // power density
            Integral { [ - jouleLosses[{T}, Norm[{d a_after_projection}],I2TH_fct[]], {T}];
                In <<nc.omega>><<nc.powered>>_TH; Integration Int_TH; Jacobian Jac_Vol_TH;  }
            {% if dm.magnet.solve.collar.transient_effects_enabled and 'collar' in areas_to_build['TH'] %}
            Integral { [pre_eddy[]* -1.0/rho[{T}] * SquNorm[Dt[CompZ[{a_after_projection}]]], {T} ];  // eddy current losses in collar
                 In <<nc.omega>><<nc.collar>>_TH; Jacobian Jac_Vol_TH; Integration Int_TH; }
            {% endif %}
            {% if dm.magnet.solve.poles.transient_effects_enabled  and 'poles' in areas_to_build['TH'] %}
            Integral { [pre_eddy[]* -1.0/rho[{T}] * SquNorm[Dt[CompZ[{a_after_projection}]]], {T} ];  // eddy current losses in the poles
                In <<nc.omega>><<nc.poles>>_TH; Jacobian Jac_Vol_TH; Integration Int_TH; } 
            {% endif %}

            Integral { [ pre_eddy[]*-1.0/rho[{T}, Norm[{d a_after_projection}]] * SquNorm[Dt[CompZ[{a_after_projection}]]], {T} ];  // eddy current losses in the coils DEBUG ALWAYS ENABLED
                In <<nc.omega>><<nc.powered>>_TH; Jacobian Jac_Vol_TH; Integration Int_TH; }

            {% if dm.magnet.geometry.thermal.with_wedges and dm.magnet.solve.wedges.transient_effects_enabled %}
            Integral { [pre_eddy[]* -1.0/rho[{T}, Norm[{d a_after_projection}]] * SquNorm[Dt[CompZ[{a_after_projection}]]], {T} ];  // eddy current losses in wedges
                 In <<nc.omega>><<nc.induced>>_TH; Jacobian Jac_Vol_TH; Integration Int_TH; } 
            {% endif %}

        {% if dm.magnet.solve.thermal.collar_cooling.enabled %}
            // cooling in the collar
            Integral { [col_heatExchCoeff[{T}, T_ref] * Dof{T},  {T}  ] ; 
                In bndCollarGaps; Integration Int_line_TH ; Jacobian Jac_Sur_TH ; }
            Integral { [-col_heatExchCoeff[{T}, T_ref] * T_ref, {T} ] ;
                In bndCollarGaps; Integration Int_line_TH ; Jacobian Jac_Sur_TH ; }

        {% endif %}
        {% if dm.magnet.geometry.thermal.use_TSA %}
            {% if not dm.magnet.geometry.thermal.use_TSA_new %}
        For tsaGroup In {1:<<len(TSAinsulation_layers_number)>>}
            For i In {0:n_ele_per_tsa_group~{tsaGroup} - 1} // loop over 1D FE elements
                For j In {1:2} // separation between vertical and horizontal
                    For k In {1:2}
                        For l In {1:2}
            Integral { [  thermalConductivityMass~{i}[{Ti~{i}~{j}~{tsaGroup}}, {Ti~{i+1}~{j}~{tsaGroup}}, delta~{i}[], k, l] *
                    Dof{d Ti~{i + k - 1}~{j}~{tsaGroup}} , {d Ti~{i + l - 1}~{j}~{tsaGroup}}];
                    In intDomain~{j}~{tsaGroup}; Integration Int_line_TH; Jacobian Jac_Sur_TH;
                }

            Integral { [thermalConductivityStiffness~{i}[{Ti~{i}~{j}~{tsaGroup}}, {Ti~{i+1}~{j}~{tsaGroup}}, delta~{i}[], k, l] *
                    Dof{Ti~{i + k - 1}~{j}~{tsaGroup}} , {Ti~{i + l - 1}~{j}~{tsaGroup}} ];
                  In intDomain~{j}~{tsaGroup}; Integration Int_line_TH; Jacobian Jac_Sur_TH;
                }
            Integral {
                  DtDof[ specificHeatCapacity~{i}[{Ti~{i}~{j}~{tsaGroup}}, {Ti~{i+1}~{j}~{tsaGroup}}, delta~{i}[], k, l] *
                    Dof{Ti~{i + k - 1}~{j}~{tsaGroup}} , {Ti~{i + l - 1}~{j}~{tsaGroup}} ];
                  In intDomain~{j}~{tsaGroup}; Integration Int_line_TH; Jacobian Jac_Sur_TH;
                }
                        EndFor  // l
                    EndFor // k
                EndFor  // j
            EndFor  // i
        EndFor  // tsaGroup
            {% else %}
                // USE TSA COLLAR
                For tsaGroup In {1:<<len(TSAinsulation_layers_number)>>} 
                    For i In {0:n_ele_per_tsa_group~{tsaGroup} - 1} // loop over 1D FE elements
                        For j In {1:2} // separation between vertical and horizontal
                            For k In {1:2}
                                For l In {1:2}
                    Integral { [ TSA_new_correction~{j}~{tsaGroup}*thermalConductivityMass~{i}[{Ti~{i}~{j}~{tsaGroup}}, {Ti~{i+1}~{j}~{tsaGroup}}, delta~{i}[], k, l] *
                            Dof{d Ti~{i + k - 1}~{j}~{tsaGroup}} , {d Ti~{i + l - 1}~{j}~{tsaGroup}}];
                            In intDomain~{j}~{tsaGroup}; Integration Int_line_TH; Jacobian Jac_Sur_TH;
                        }
                    Integral { [  TSA_new_correction~{j}~{tsaGroup}*thermalConductivityStiffness~{i}[{Ti~{i}~{j}~{tsaGroup}}, {Ti~{i+1}~{j}~{tsaGroup}}, delta~{i}[], k, l] *
                            Dof{Ti~{i + k - 1}~{j}~{tsaGroup}} , {Ti~{i + l - 1}~{j}~{tsaGroup}} ];
                        In intDomain~{j}~{tsaGroup}; Integration Int_line_TH; Jacobian Jac_Sur_TH;
                        }
                    Integral {
                            DtDof[ TSA_new_correction~{j}~{tsaGroup}*specificHeatCapacity~{i}[{Ti~{i}~{j}~{tsaGroup}}, {Ti~{i+1}~{j}~{tsaGroup}}, delta~{i}[], k, l] *
                            Dof{Ti~{i + k - 1}~{j}~{tsaGroup}} , {Ti~{i + l - 1}~{j}~{tsaGroup}} ];
                        In intDomain~{j}~{tsaGroup}; Integration Int_line_TH; Jacobian Jac_Sur_TH;
                        }
                                EndFor  // l
                            EndFor // k
                        EndFor  // j
                    EndFor  // i
                EndFor  // tsaGroup
            {% endif %}
            {% for nr, n_ele in enumerate(rm_TH.thin_shells.quench_heaters.layers_number) %}
                {% set qu_nr = nr + len(rm_TH.thin_shells.insulation_types.thin_shells) %}

        For i In {0:<<n_ele-1>>} // loop over 1D FE elements
            For j In {1:2} // separation between vertical and horizontal
                For k In {1:2}
            Integral { [- powerDensity~{i}[{Ti~{i}~{j}~{<<qu_nr + 1>>}}, {Ti~{i+1}~{j}~{<<qu_nr + 1>>}}, delta~{i}[], k], {Ti~{i + k - 1}~{j}~{<<qu_nr + 1>>}} ];
                  In intDomain~{j}~{<<qu_nr + 1>>}; Integration Int_line_TH; Jacobian Jac_Sur_TH; }
                EndFor //k
            EndFor  // j
        EndFor  // i
            {% endfor %}

        // one fewer for loop cause no horVerLayers --> but one more bc of function for N_eleL
        If (num_robin > 0)
            For tsaGroup In {1:<<len(TSAinsulation_layers_number)>>}
            // ----------------- ROBIN -----------------------------------------------
                For j In {1:2} // separation between vertical and horizontal
                    For x In {1:2}
                        For a In {1:2}
            Integral { [heatExchCoeff[{Ti~{outerElem~{j}~{x}~{a}~{tsaGroup}}~{j}~{tsaGroup}}, Tinf[]] * Dof{Ti~{outerElem~{j}~{x}~{a}~{tsaGroup}}~{j}~{tsaGroup}},
                   {Ti~{outerElem~{j}~{x}~{a}~{tsaGroup}}~{j}~{tsaGroup}} ] ;
                   In bndRobinInt~{j}~{x}~{a}~{tsaGroup}; Integration Int_line_TH ; Jacobian Jac_Sur_TH ; }

            Integral { [-heatExchCoeff[{Ti~{outerElem~{j}~{x}~{a}~{tsaGroup}}~{j}~{tsaGroup}}, Tinf[]] * Tinf[], {Ti~{outerElem~{j}~{x}~{a}~{tsaGroup}}~{j}~{tsaGroup}} ] ;
                    In bndRobinInt~{j}~{x}~{a}~{tsaGroup}; Integration Int_line_TH ; Jacobian Jac_Sur_TH ; }
                        EndFor
                    EndFor
                EndFor
            EndFor
        EndIf

        // ----------------- NEUMANN -----------------------------------------------
        // one fewer for loop cause no horVerLayers --> but one more bc of function for N_eleL
        If (num_neumann > 0)
            For tsaGroup In {1:<<len(TSAinsulation_layers_number)>>}
            // ----------------- Neumann -----------------------------------------------
                For j In {1:2} // separation between vertical and horizontal
                    For x In {1:2}
                        For a In {1:2}
            Integral { [-heatFlux[],
                    {Ti~{outerElem~{j}~{x}~{a}~{tsaGroup}}~{j}~{tsaGroup}} ] ;
                    In bndNeuInt~{j}~{x}~{a}~{tsaGroup}; Integration Int_line_TH ; Jacobian Jac_Sur_TH ; }
                        EndFor
                    EndFor
                EndFor
            EndFor
        EndIf

        {% else %} {# not TSA #}

        // Neumann
            {% for nr, value in enumerate(rm_TH.boundaries.thermal.heat_flux.bc.value) %}
            Integral { [- <<value>> , {T} ] ;
                In {% if dm.magnet.solve.thermal.He_cooling.sides != 'external' and nr == 0 %} general_adiabatic {% else %} <<list(dm.magnet.solve.thermal.overwrite_boundary_conditions.heat_flux)[nr - 1 if dm.magnet.solve.thermal.He_cooling.sides != 'external' else nr]>> {% endif %}; Integration Int_line_TH ; Jacobian Jac_Sur_TH ; }
            {% endfor %}

        // Robin
        // n * kappa grad (T) = h (T - Tinf) becomes two terms since GetDP can only
        // handle linear and not affine terms
        // NOTE: signs might be switched
            {% for nr, values in enumerate(rm_TH.boundaries.thermal.cooling.bc.values) %}
                {% if isinstance(values[0], str) %}
            Integral { [<<values[0]>>[{T}, <<values[1]>>] * Dof{T}, {T} ] ;
                In {% if dm.magnet.solve.thermal.He_cooling.enabled and nr == 0 %} general_cooling {% else %} <<list(dm.magnet.solve.thermal.overwrite_boundary_conditions.cooling)[nr - 1 if dm.magnet.solve.thermal.He_cooling.enabled else nr]>> {% endif %}; Integration Int_line_TH ; Jacobian Jac_Sur_TH ; }
            Integral { [-<<values[0]>>[{T}, <<values[1]>>] * <<values[1]>> , {T} ] ;
                In {% if dm.magnet.solve.thermal.He_cooling.enabled and nr == 0 %} general_cooling {% else %} <<list(dm.magnet.solve.thermal.overwrite_boundary_conditions.cooling)[nr - 1 if dm.magnet.solve.thermal.He_cooling.enabled else nr]>> {% endif %}; Integration Int_line_TH ; Jacobian Jac_Sur_TH ; }
                {% else %}
            Integral { [<<values[0]>> * Dof{T}, {T} ] ;
                In {% if dm.magnet.solve.thermal.He_cooling.enabled and nr == 0 %} general_cooling {% else %} <<list(dm.magnet.solve.thermal.overwrite_boundary_conditions.cooling)[nr - 1 if dm.magnet.solve.thermal.He_cooling.enabled else nr]>> {% endif %}; Integration Int_line_TH ; Jacobian Jac_Sur_TH ; }
            Integral { [-<<values[0]>> * <<values[1]>> , {T} ] ;
                In {% if dm.magnet.solve.thermal.He_cooling.enabled and nr == 0 %} general_cooling {% else %} <<list(dm.magnet.solve.thermal.overwrite_boundary_conditions.cooling)[nr - 1 if dm.magnet.solve.thermal.He_cooling.enabled else nr]>> {% endif %}; Integration Int_line_TH ; Jacobian Jac_Sur_TH ; }
                {% endif %}
            {% endfor %}
        {% endif %}
        }
    }
    {% endif %}
}

Resolution {
    { Name resolution;
        System {
    {%  if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Mag_dyn' or SIM_MODE == 'Mag_dyn_0'%}
            { Name Sys_Mag_dyn; NameOfFormulation Magnetodynamics_a_2D; NameOfMesh "<<mf['EM']>>"; }
    {%  else %}
            { Name Sys_Mag_static; NameOfFormulation Magnetostatics_a_2D; NameOfMesh "<<mf['EM']>>"; }
    {%  endif %}
    {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Th_Mag_sta' %}
            { Name Sys_The; NameOfFormulation Thermal_T; NameOfMesh "<<mf['TH']>>"; }
            { Name sys_Mag_projection; NameOfFormulation Projection_EM_to_TH; NameOfMesh "<<mf['TH']>>";}
    {%if dm.quench_protection.quench_heaters.quench_propagation == "2Dx1D" or dm.quench_protection.e_cliq.quench_propagation == "2Dx1D"%}
            { Name sys_QR_EM; NameOfFormulation Quench_Prop_EM; NameOfMesh "<<mf['EM']>>";}
            { Name sys_QR_TH; NameOfFormulation Quench_Prop_TH; NameOfMesh "<<mf['TH']>>";}
    {% endif %}
    {% if USE_THERMAL_PROJECTION %}
            { Name sys_The_projection; NameOfFormulation Projection_TH_to_EM; NameOfMesh "<<mf['EM']>>";} 
    {% endif %}
    {% endif %}
        }
        Operation{
            {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Th_Mag_sta' or SIM_MODE == 'Mag_dyn' or SIM_MODE == 'Mag_dyn_0'%}
            SetTime[{% if SIM_MODE == 'Th_Mag_sta'%} <<dm.magnet.solve.thermal.time_stepping.initial_time>>
                    {% elif SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' %} <<dm.magnet.solve.time_stepping.initial_time>>
                    {% else %}<<dm.magnet.solve.electromagnetics.time_stepping.initial_time>>{% endif %}];
            {% endif %}
            // Initialize times to zero
            Evaluate[$tg_cumul_cpu = 0, $ts_cumul_cpu = 0, $tg_cumul_wall = 0, $ts_cumul_wall = 0,$tp_cumul_wall = 0, $tp_cumul_cpu = 0];
            Evaluate[$tg_wall = 0, $tg_cpu = 0, $ts_wall = 0, $ts_cpu = 0, $tpr_wall = 0, $tpr_cpu = 0, $tp_wall = 0, $tp_cpu = 0];
            Evaluate[$tg1_wall = 0, $tg2_wall = 0, $tg3_wall = 0, $tg4_wall = 0, $tg1_cpu = 0, $tg2_cpu = 0, $tg3_cpu = 0, $tg4_cpu = 0];
            Evaluate[$ts1_wall = 0, $ts2_wall = 0, $ts3_wall = 0, $ts4_wall = 0, $ts1_cpu = 0 , $ts2_cpu = 0, $ts3_cpu = 0, $ts4_cpu = 0];
            Evaluate[$tpr1_wall = 0, $tpr2_wall = 0, $tpr1_cpu = 0, $tpr2_cpu = 0];
            Print["timestep,gen_wall,gen_cpu,sol_wall,sol_cpu,pos_wall,pos_cpu,gen_wall_cumul,gen_cpu_cumul,sol_wall_cumul,sol_cpu_cumul,pos_wall_cumul,pos_cpu_cumul", File "computation_times.csv"];
            {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Mag_dyn' or SIM_MODE == 'Mag_dyn_0'%}
            Print["timestep,E_mag [J]", File "E_mag.csv"];
            {% endif %}
            

            {% if USE_THERMAL_PROJECTION %}
            PostOperation[T_avg_collar_init]; // initialise
            Generate[sys_The_projection];
            {% endif %}    

            {% if SIM_MODE == 'Th_Mag_sta' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Th_Mag' %}
            CreateDirectory["T_avg"];
                {% if dm.magnet.geometry.thermal.with_wedges %}
            PostOperation[T_avg_init];
                {% endif %}
            {% endif %}

            {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Mag_dyn' or SIM_MODE == 'Mag_dyn_0' %}
            InitSolution[Sys_Mag_dyn];
                {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' %}
            InitSolution[Sys_The];
                    {% if SIM_MODE != 'Th_Mag' %}
            //CreateDirectory["T_avg"];
            PostOperation[T_avg];
                    {% endif %}
                {% endif %}
                {% if dm.circuit.field_circuit and (SIM_MODE == 'Th_Mag' or SIM_MODE == 'Mag_dyn') %}
            PostOperation[circuit_coupling];
                {% endif %}
            {% else %}
            InitSolution[Sys_Mag_static];            
                {% if SIM_MODE == 'Th_Mag_sta' %}
                {% if dm.circuit.field_circuit %}
                <<cc_macros2.resolution_FCC(dm,rm_EM,flag_active,ESC_dict,ECLIQ_dict)>>
                {% endif %}
            InitSolution[Sys_The];
            //CreateDirectory["T_avg"];
            PostOperation[T_avg];
                {% endif %}
            IterativeLoopN[<<dm.magnet.solve.electromagnetics.non_linear_solver.max_iterations>>, <<dm.magnet.solve.electromagnetics.non_linear_solver.relaxation_factor>>,
                            {%- if dm.circuit.field_circuit%} 
                            PostOperation{ { conv2_sta, <<dm.magnet.solve.electromagnetics.time_stepping.rel_tol_time>>, <<dm.magnet.solve.electromagnetics.time_stepping.abs_tol_time>>, <<dm.magnet.solve.electromagnetics.time_stepping.norm_type>> }}{%endif -%}
                            System { { Sys_Mag_static, <<dm.magnet.solve.electromagnetics.non_linear_solver.rel_tolerance>>, <<dm.magnet.solve.electromagnetics.non_linear_solver.abs_tolerance>>, Solution <<dm.magnet.solve.electromagnetics.non_linear_solver.norm_type>> } }] 
            {                    
                Evaluate[ $tg1_wall = GetWallClockTime[], $tg1_cpu = GetCpuTime[] ];
                 GenerateJac[Sys_Mag_static]; 
                Evaluate[ $tg2_wall = GetWallClockTime[], $tg2_cpu = GetCpuTime[] ];

                Evaluate[ $ts1_wall = GetWallClockTime[], $ts1_cpu = GetCpuTime[] ];
                 SolveJac[Sys_Mag_static];
                Evaluate[ $ts2_wall = GetWallClockTime[], $ts2_cpu = GetCpuTime[] ];
            }
            Evaluate[ $tp1_wall = GetWallClockTime[], $tp1_cpu = GetCpuTime[] ];
            PostOperation[Map_a_sta];
            Evaluate[ $tp2_wall = GetWallClockTime[], $tp2_cpu = GetCpuTime[] ];
                {% if dm.circuit.field_circuit and SIM_MODE == 'Mag_sta' %}
              <<cc_macros2.resolution_FCC(dm,rm_EM,flag_active,ESC_dict,ECLIQ_dict)>>
              PostOperation[circuit_coupling_sta];
                {% endif %}
            Evaluate[$tg_wall = $tg_wall + $tg2_wall - $tg1_wall + $tg4_wall - $tg3_wall, $tg_cpu = $tg_cpu + $tg2_cpu - $tg1_cpu + $tg4_cpu - $tg3_cpu, $ts_wall = $ts_wall + $ts2_wall - $ts1_wall + $ts4_wall - $ts3_wall, $ts_cpu = $ts_cpu + $ts2_cpu - $ts1_cpu + $ts4_cpu - $ts3_cpu, $tpr_wall = $tpr_wall + $tpr2_wall - $tpr1_wall, $tpr_cpu = $tpr_cpu + $tpr2_cpu - $tpr1_cpu,$tp_wall = $tp_wall + $tp2_wall - $tp1_wall,$tp_cpu = $tp_cpu + $tp2_cpu - $tp1_cpu ];
            // cumulated times
            Evaluate[ $tg_cumul_wall = $tg_cumul_wall + $tg_wall, $tg_cumul_cpu = $tg_cumul_cpu + $tg_cpu, $ts_cumul_wall = $ts_cumul_wall + $ts_wall, $ts_cumul_cpu = $ts_cumul_cpu + $ts_cpu, $tp_cumul_wall = $tp_cumul_wall + $tp_wall, $tp_cumul_cpu = $tp_cumul_cpu + $tp_cpu];

            // print to file
            Print[{$TimeStep, $tg_wall, $tg_cpu, $ts_wall, $ts_cpu, $tp_wall, $tp_cpu, $tg_cumul_wall, $tg_cumul_cpu, $ts_cumul_wall, $ts_cumul_cpu, $tp_cumul_wall, $tp_cumul_cpu}, Format "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g", File "computation_times.csv"];

                {% if SIM_MODE == 'Th_Mag_sta' %}
              Generate[sys_Mag_projection]; Solve[sys_Mag_projection]; 
              SaveSolution[sys_Mag_projection]; //PostOperation[b_after_projection_pos];
                {% endif %}
            {% endif %}

            {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Th_Mag_sta' %}
            SetExtrapolationOrder[0];
            {% if SIM_MODE != 'Th_Mag'%}
            CreateDirectory["I2TH"];
            {% endif %}
            PostOperation[GetI2TH];
            {% endif %}
            {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Th_Mag_sta' or SIM_MODE == 'Mag_dyn' or SIM_MODE == 'Mag_dyn_0' %}
            {% if dm.circuit.field_circuit and (SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Mag_dyn_0')%}
            <<cc_macros2.resolution_FCC(dm,rm_EM,flag_active,ESC_dict,ECLIQ_dict)>>
            PostOperation[circuit_coupling];
            {% endif %}
            TimeLoopAdaptive[
                {% if dm.magnet.solve.thermal.solve_type and dm.magnet.solve.electromagnetics.solve_type == 'transient' %}
                            <<dm.magnet.solve.time_stepping.initial_time>>, <<dm.magnet.solve.time_stepping.final_time>>, <<dm.magnet.solve.time_stepping.initial_time_step>>, <<dm.magnet.solve.time_stepping.min_time_step>>, <<dm.magnet.solve.time_stepping.max_time_step>>, "<<dm.magnet.solve.time_stepping.integration_method>>", List[Breakpoints],
                            System { { Sys_The, <<dm.magnet.solve.time_stepping.rel_tol_time[-1]>>, <<dm.magnet.solve.time_stepping.abs_tol_time[-1]>>, <<dm.magnet.solve.time_stepping.norm_type[-1]>> } } PostOperation { { conv, <<dm.magnet.solve.time_stepping.rel_tol_time[0]>>, <<dm.magnet.solve.time_stepping.abs_tol_time[0]>>, <<dm.magnet.solve.time_stepping.norm_type[0]>> }{%if dm.circuit.field_circuit%}{ conv2, <<dm.magnet.solve.time_stepping.rel_tol_time[1]>>, <<dm.magnet.solve.time_stepping.abs_tol_time[1]>>, <<dm.magnet.solve.time_stepping.norm_type[1]>> }{%endif%}}
                {% elif dm.magnet.solve.thermal.solve_type %}
                            <<dm.magnet.solve.thermal.time_stepping.initial_time>>, <<dm.magnet.solve.thermal.time_stepping.final_time>>, <<dm.magnet.solve.thermal.time_stepping.initial_time_step>>, <<dm.magnet.solve.thermal.time_stepping.min_time_step>>, <<dm.magnet.solve.thermal.time_stepping.max_time_step>>, "<<dm.magnet.solve.thermal.time_stepping.integration_method>>", List[Breakpoints],
                            System { { Sys_The, <<dm.magnet.solve.thermal.time_stepping.rel_tol_time>>, <<dm.magnet.solve.thermal.time_stepping.abs_tol_time>>, <<dm.magnet.solve.thermal.time_stepping.norm_type>> } }
                {% else %}
                            <<dm.magnet.solve.electromagnetics.time_stepping.initial_time>>, <<dm.magnet.solve.electromagnetics.time_stepping.final_time>>, <<dm.magnet.solve.electromagnetics.time_stepping.initial_time_step>>, <<dm.magnet.solve.electromagnetics.time_stepping.min_time_step>>, <<dm.magnet.solve.electromagnetics.time_stepping.max_time_step>>, "<<dm.magnet.solve.electromagnetics.time_stepping.integration_method>>", List[Breakpoints],
                            PostOperation { { conv, <<dm.magnet.solve.electromagnetics.time_stepping.rel_tol_time>>, <<dm.magnet.solve.electromagnetics.time_stepping.abs_tol_time>>, <<dm.magnet.solve.electromagnetics.time_stepping.norm_type>> } {%  if dm.circuit.field_circuit  %} { conv2, <<dm.magnet.solve.electromagnetics.time_stepping.rel_tol_time>>, <<dm.magnet.solve.electromagnetics.time_stepping.abs_tol_time>>, <<dm.magnet.solve.electromagnetics.time_stepping.norm_type>> }{%endif%}}
                {% endif %}
            ]{
                
                IterativeLoopN[
                    {% if SIM_MODE == 'Th_Mag_sta' %} 
                    <<dm.magnet.solve.thermal.non_linear_solver.max_iterations>>, <<dm.magnet.solve.thermal.non_linear_solver.relaxation_factor>>,
                    System { { Sys_The, <<dm.magnet.solve.thermal.non_linear_solver.rel_tolerance>>, <<dm.magnet.solve.thermal.non_linear_solver.abs_tolerance>>, Solution <<dm.magnet.solve.thermal.non_linear_solver.norm_type>> } }
                    {% elif SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' %}
                    <<dm.magnet.solve.electromagnetics.non_linear_solver.max_iterations>>, <<dm.magnet.solve.electromagnetics.non_linear_solver.relaxation_factor>>,
                    PostOperation { { conv, <<dm.magnet.solve.electromagnetics.non_linear_solver.rel_tolerance>>, <<dm.magnet.solve.electromagnetics.non_linear_solver.abs_tolerance>>, <<dm.magnet.solve.electromagnetics.non_linear_solver.norm_type>> }{%if dm.circuit.field_circuit%} { conv2, <<dm.magnet.solve.electromagnetics.time_stepping.rel_tol_time>>, <<dm.magnet.solve.electromagnetics.time_stepping.abs_tol_time>>, <<dm.magnet.solve.electromagnetics.time_stepping.norm_type>> }{%endif%}} System { { Sys_The, <<dm.magnet.solve.thermal.non_linear_solver.rel_tolerance>>, <<dm.magnet.solve.thermal.non_linear_solver.abs_tolerance>>, Solution <<dm.magnet.solve.thermal.non_linear_solver.norm_type>> } }
                    {% else %}
                    <<dm.magnet.solve.electromagnetics.non_linear_solver.max_iterations>>, <<dm.magnet.solve.electromagnetics.non_linear_solver.relaxation_factor>>,
                    PostOperation { { conv, <<dm.magnet.solve.electromagnetics.non_linear_solver.rel_tolerance>>, <<dm.magnet.solve.electromagnetics.non_linear_solver.abs_tolerance>>, <<dm.magnet.solve.electromagnetics.non_linear_solver.norm_type>> }{%  if dm.circuit.field_circuit  %} { conv2, <<dm.magnet.solve.electromagnetics.time_stepping.rel_tol_time>>, <<dm.magnet.solve.electromagnetics.time_stepping.abs_tol_time>>, <<dm.magnet.solve.electromagnetics.time_stepping.norm_type>> }{%endif%}}
                  // System { { Sys_Mag, <<dm.magnet.solve.electromagnetics.time_stepping.rel_tol_time>>, <<dm.magnet.solve.electromagnetics.time_stepping.abs_tol_time>>, Solution <<dm.magnet.solve.electromagnetics.time_stepping.norm_type>> } } 
                    {% endif %}
                ]{
                    {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Mag_dyn' or SIM_MODE == 'Mag_dyn_0'  %}
                    Evaluate[ $tg1_wall = GetWallClockTime[], $tg1_cpu = GetCpuTime[] ];
                    GenerateJac Sys_Mag_dyn ;
                    Evaluate[ $tg2_wall = GetWallClockTime[], $tg2_cpu = GetCpuTime[] ];

                    Evaluate[ $ts1_wall = GetWallClockTime[], $ts1_cpu = GetCpuTime[] ];
                    SolveJac Sys_Mag_dyn;
                    Evaluate[ $ts2_wall = GetWallClockTime[], $ts2_cpu = GetCpuTime[] ];
                    {% endif %}
                    {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' %}
                    Evaluate[ $tpr1_wall = GetWallClockTime[], $tpr1_cpu = GetCpuTime[] ];
                    Generate[sys_Mag_projection]; Solve[sys_Mag_projection]; 
                    Evaluate[ $tpr2_wall = GetWallClockTime[], $tpr2_cpu = GetCpuTime[] ];
                    SaveSolution[sys_Mag_projection]; //PostOperation[b_after_projection_pos];
                    {% endif %}
                    {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Th_Mag_sta' %}
                    Evaluate[ $tg3_wall = GetWallClockTime[], $tg3_cpu = GetCpuTime[] ];
                    GenerateJac Sys_The ;
                    Evaluate[ $tg4_wall = GetWallClockTime[], $tg4_cpu = GetCpuTime[] ];

                    Evaluate[ $ts3_wall = GetWallClockTime[], $ts3_cpu = GetCpuTime[] ];
                    SolveJac Sys_The;
                    Evaluate[ $ts4_wall = GetWallClockTime[], $ts4_cpu = GetCpuTime[] ];
                    {% endif %}
                    // add to solution times of previous rejected time steps
                    Evaluate[$tg_wall = $tg_wall + $tg2_wall - $tg1_wall + $tg4_wall - $tg3_wall, $tg_cpu = $tg_cpu + $tg2_cpu - $tg1_cpu + $tg4_cpu - $tg3_cpu, $ts_wall = $ts_wall + $ts2_wall - $ts1_wall + $ts4_wall - $ts3_wall, $ts_cpu = $ts_cpu + $ts2_cpu - $ts1_cpu + $ts4_cpu - $ts3_cpu, $tpr_wall = $tpr_wall + $tpr2_wall - $tpr1_wall, $tpr_cpu = $tpr_cpu + $tpr2_cpu - $tpr1_cpu ];
                    {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_sta' %}
                        {% if dm.magnet.solve.thermal.enforce_init_temperature_as_minimum %}
                    SolutionSetMin[Sys_The, <<dm.magnet.solve.thermal.init_temperature>>];
                        {% endif %}
                    {% endif %}

                  }
                  
                // Check if the solution is NaN and remove it
                Test[$KSPResidual != $KSPResidual]{
                    Print["Critical: Removing NaN solution from the solution vector."];
                {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Th_Mag_sta' %}
                    RemoveLastSolution[Sys_The];
                {% endif %}
                {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Mag_dyn' or SIM_MODE == 'Mag_dyn_0' %}
                    RemoveLastSolution[Sys_Mag_dyn];
                {% endif %}
                }
            }{
                {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Th_Mag_sta' %}

                    {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' %}
                    PostOperation[GetI2TH];
                    PostOperation[T_avg];

                    SaveSolution[Sys_Mag_dyn];
                    {% endif %}
                    SaveSolution[Sys_The];


                    Evaluate[ $tp1_wall = GetWallClockTime[], $tp1_cpu = GetCpuTime[] ];
                    {% if (not dm.magnet.postproc.thermal.save_txt_at_the_end and dm.magnet.postproc.thermal.output_time_steps_txt) %}
                    // print average temperature
                        {% if dm.magnet.postproc.thermal.output_time_steps_txt > 1%}
                    Test[$TimeStep > 1] {
                            PostOperation[T_avg];
                            }
                        {% else %}
                    PostOperation[T_avg];
                        {% endif %}
                    {% endif %}

                    {% if (not dm.magnet.postproc.thermal.save_pos_at_the_end and dm.magnet.postproc.thermal.output_time_steps_pos) %}
                    // print temperature map
                        {% if dm.magnet.postproc.thermal.output_time_steps_pos > 1%}
                    Test[$TimeStep > 1] {
                    PostOperation[Map_T];
                    }
                        {% else %}
                    PostOperation[Map_T];
                            {% if dm.magnet.solve.electromagnetics.solve_type == 'transient' %}
                    PostOperation[Map_a];
                            {% endif %}
                        {% endif %}
                    {% endif %}
                    {% if 'collar' in areas_to_build['TH'] %}
                    PostOperation[PrintMaxTemp_col]; // save maximum temperature in register 1
                    {% endif %}
                    PostOperation[PrintMaxTemp]; // save maximum temperature in register 1
                    Evaluate[ $tp2_wall = GetWallClockTime[], $tp2_cpu = GetCpuTime[] ];

                    Evaluate[ $tp_wall = $tp2_wall - $tp1_wall, $tp_cpu = $tp2_cpu - $tp1_cpu ];

                    // cumulated times
                    Evaluate[ $tg_cumul_wall = $tg_cumul_wall + $tg_wall, $tg_cumul_cpu = $tg_cumul_cpu + $tg_cpu, $ts_cumul_wall = $ts_cumul_wall + $ts_wall, $ts_cumul_cpu = $ts_cumul_cpu + $ts_cpu, $tp_cumul_wall = $tp_cumul_wall + $tp_wall, $tp_cumul_cpu = $tp_cumul_cpu + $tp_cpu];

                    // print to file
                    Print[{$TimeStep, $tg_wall, $tg_cpu, $ts_wall, $ts_cpu, $tp_wall, $tp_cpu, $tg_cumul_wall, $tg_cumul_cpu, $ts_cumul_wall, $ts_cumul_cpu, $tp_cumul_wall, $tp_cumul_cpu}, Format "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g", File "computation_times.csv"];

                    // reset after accepted time step
                    Evaluate[$tg_wall = 0, $tg_cpu = 0, $ts_wall = 0, $ts_cpu = 0];

                    // check if maximum temperature is reached
                    {# raw block needed since use of # in following code #}
                    {% raw %}
                    Print[{#1}, Format "Maximum temperature: %g "];
                    Test[#1 > stop_temperature] {
                        Break[];
                    }
                    {% endraw %}
                {% else %}
                // save solution to .res file
                SaveSolution[Sys_Mag_dyn];

            
                // cumulated times
                Evaluate[ $tg_cumul_wall = $tg_cumul_wall + $tg_wall, $tg_cumul_cpu = $tg_cumul_cpu + $tg_cpu, $ts_cumul_wall = $ts_cumul_wall + $ts_wall, $ts_cumul_cpu = $ts_cumul_cpu + $ts_cpu, $tp_cumul_wall = $tp_cumul_wall + $tp_wall, $tp_cumul_cpu = $tp_cumul_cpu + $tp_cpu];
            
                // print to file
                Print[{$TimeStep, $tg_wall, $tg_cpu, $ts_wall, $ts_cpu,$tp_wall,$tp_cpu,$tg_cumul_wall,$tg_cumul_cpu,$ts_cumul_wall,$ts_cumul_cpu,$tp_cumul_wall,$tp_cumul_cpu}, Format "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g", File "computation_times.csv"];
            
                // reset after accepted time step
                Evaluate[$tg_wall = 0, $tg_cpu = 0, $ts_wall = 0, $ts_cpu = 0];
                
                {% endif %}
                {% if (dm.quench_protection.quench_heaters.quench_propagation == "2Dx1D" or dm.quench_protection.e_cliq.quench_propagation == "2Dx1D") and dm.magnet.solve.thermal.solve_type%}
                Generate[sys_QR_TH];
                PostOperation[Map_R_quench_TH];
                Generate[sys_QR_EM];
                PostOperation[Map_R_quench];
                {% endif %}

            }
                {% if (SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Mag_dyn' or SIM_MODE == 'Mag_dyn_0') and dm.magnet.postproc.electromagnetics.output_time_steps_pos %}
                Evaluate[ $tp1_wall = GetWallClockTime[], $tp1_cpu = GetCpuTime[] ];
                PostOperation[Map_a];

                {% endif %}
                {% if (SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Th_Mag_sta') and dm.magnet.postproc.thermal.output_time_steps_pos  %}
                PostOperation[Map_T];
                {% endif %}
                {% if dm.circuit.field_circuit and dm.magnet.postproc.electromagnetics.output_time_steps_pos %}
                {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Mag_dyn' or SIM_MODE == 'Mag_dyn_0' %}
            PostOperation[circuit_coupling];
                {% endif %}
                {% if SIM_MODE == 'Th_Mag_sta' or SIM_MODE == 'Mag_sta' %}
                PostOperation[circuit_coupling_sta];
                {% endif %}
                {% endif %}
            Evaluate[ $tp2_wall = GetWallClockTime[], $tp2_cpu = GetCpuTime[] ];

            Evaluate[ $tp_wall = $tp2_wall - $tp1_wall, $tp_cpu = $tp2_cpu - $tp1_cpu ];
            // cumulated times
            Evaluate[  $tp_cumul_wall = $tp_cumul_wall + $tp_wall, $tp_cumul_cpu = $tp_cumul_cpu + $tp_cpu];
            
            // print to file
            Print[{$TimeStep, $tg_wall, $tg_cpu, $ts_wall, $ts_cpu,$tp_wall,$tp_cpu,$tg_cumul_wall,$tg_cumul_cpu,$ts_cumul_wall,$ts_cumul_cpu,$tp_cumul_wall,$tp_cumul_cpu}, Format "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g", File "computation_times.csv"];

            // PostOperation[b_thermal]; 
                        
            {% endif %}

            
        }

    }
    {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Mag_dyn' %}
    { Name Static_2_Dynamic; 
        System {
            { Name Sys_Mag_static; NameOfFormulation Magnetostatics_a_2D; NameOfMesh "<<mf['EM']>>"; DestinationSystem Sys_Mag_dyn;}
            { Name Sys_Mag_dyn; NameOfFormulation Magnetodynamics_a_2D; NameOfMesh "<<mf['EM']>>"; }
            {% if SIM_MODE == 'Th_Mag' %}
            { Name Sys_The; NameOfFormulation Thermal_T; NameOfMesh "<<mf['TH']>>"; }
            {% endif %}
        }
        Operation {
            SetTime[{% if dm.magnet.solve.thermal.solve_type %}<<dm.magnet.solve.time_stepping.initial_time>>{% else %}<<dm.magnet.solve.electromagnetics.time_stepping.initial_time>>{% endif %}];
            InitSolution[Sys_Mag_static];
            {% if SIM_MODE == 'Th_Mag' %}
            InitSolution[Sys_The];
            CreateDirectory["T_avg"];
            PostOperation[T_avg];
            {% endif %}
            SaveSolution[Sys_Mag_static];
            IterativeLoopN[<<dm.magnet.solve.electromagnetics.non_linear_solver.max_iterations>>, <<dm.magnet.solve.electromagnetics.non_linear_solver.relaxation_factor>>,
                {%if dm.circuit.field_circuit%}PostOperation{ { conv2_sta, <<dm.magnet.solve.electromagnetics.time_stepping.rel_tol_time>>, <<dm.magnet.solve.electromagnetics.time_stepping.abs_tol_time>>, <<dm.magnet.solve.electromagnetics.time_stepping.norm_type>> }}{%endif%} System { { Sys_Mag_static, <<dm.magnet.solve.electromagnetics.non_linear_solver.rel_tolerance>>, <<dm.magnet.solve.electromagnetics.non_linear_solver.abs_tolerance>>, Solution <<dm.magnet.solve.electromagnetics.non_linear_solver.norm_type>> } }] { 
            GenerateJac[Sys_Mag_static];
            SolveJac[Sys_Mag_static];
            }
            SaveSolution[Sys_Mag_static];
            PostOperation[Map_a_sta];
            {% if dm.circuit.field_circuit%}
            <<cc_macros2.resolution_FCC(dm,rm_EM,flag_active,ESC_dict,ECLIQ_dict)>>
            PostOperation[circuit_coupling_sta];
            {% endif %}
            {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Mag_dyn' %}
            CreateDirectory["I2TH"];
            PostOperation[GetI2TH_sta];
            {% endif %}
            TransferSolution[Sys_Mag_static];
        }
    }
    {% endif %}

}

PostProcessing {
    {% if  SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_sta' or SIM_MODE == 'Mag_dyn' or SIM_MODE == 'Mag_sta'%}
    { Name MagSta_a_2D; NameOfFormulation Magnetostatics_a_2D; NameOfSystem Sys_Mag_static;
        Quantity {
            { Name a;
                Value {
                Term { [ {a} ]; In <<nc.omega>>_EM; Jacobian Jac_Vol_EM; }
                }
            }
            { Name az;
                Value {
                Term { [ CompZ[{a}] ]; In <<nc.omega>>_EM; Jacobian Jac_Vol_EM; }
                }
            }
            { Name b;
                Value {
                Term { [ {d a} ]; In <<nc.omega>>_EM; Jacobian Jac_Vol_EM; }
                }
            }
            { Name h;
                Value {
                Term { [ nu[{d a}] * {d a} ]; In <<nc.omega>>_EM; Jacobian Jac_Vol_EM; }
                }
            }
            {% if dm.circuit.field_circuit%}
            <<cc_macros2.postPr_FCC(nc,dm,flag_active,init_ht,end_ht,aux)>>
            {% else %}
                { Name js ;
                Value {
                    Term { [ {is}*sign_fct[]/area_fct[] ]; In <<nc.omega>><<nc.powered>>_EM; Jacobian Jac_Vol_EM; }
                }
                }
            {% endif %}
        }
    }
    {% endif %}


    {% if  SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Mag_dyn' or SIM_MODE == 'Mag_dyn_0' %}
    { Name MagDyn_a_2D; NameOfFormulation Magnetodynamics_a_2D; NameOfSystem Sys_Mag_dyn;
        Quantity {
            { Name a;
                Value {
                Term { [ {a} ]; In <<nc.omega>>_EM; Jacobian Jac_Vol_EM; }
                }
            }
            { Name az;
                Value {
                Term { [ CompZ[{a}] ]; In <<nc.omega>>_EM; Jacobian Jac_Vol_EM; }
                }
            }
            { Name b;
                Value {
                Term { [ {d a} ]; In <<nc.omega>>_EM; Jacobian Jac_Vol_EM; }
                }
            }
            { Name h;
                Value {
                Term { [ nu[{d a}] * {d a} ]; In <<nc.omega>>_EM; Jacobian Jac_Vol_EM; }
                }
            }
            { Name E_mag;
                Value {
                Integral { Type Global; [{d a}* {d a} * (nu[{d a}]  /2 ) ]; In <<nc.omega>>_EM; Jacobian Jac_Vol_EM; Integration Int_EM; }
                }
            }
        {% if dm.magnet.solve.thermal.solve_type %}
            { Name jOverJc ;
                Value {
                Term { [ {is}/area_fct[] * 1/(criticalCurrentDensity[T_EM_fct[], {d a}] + 1) ] ; In <<nc.omega>><<nc.conducting>>_EM ; Jacobian Jac_Vol_EM ; }
                }
            }
        {% endif %}
        {% if dm.circuit.field_circuit %}
        <<cc_macros2.postPr_FCC(nc,dm,flag_active,init_ht,end_ht,aux)>>
        {% else %}
            { Name js ;
            Value {
                Term { [ {is}*sign_fct[]/area_fct[] ]; In <<nc.omega>><<nc.powered>>_EM; Jacobian Jac_Vol_EM; }
            }
            }
        {% endif %}
        }
    }
    {% if (dm.quench_protection.quench_heaters.quench_propagation == "2Dx1D" or dm.quench_protection.e_cliq.quench_propagation == "2Dx1D") and dm.magnet.solve.thermal.solve_type%}
    { Name Post_R_Quench_EM; NameOfFormulation Magnetodynamics_a_2D; NameOfSystem Sys_Mag_dyn;
        Quantity {
                { Name R_Quench_EM;
                Value {
                Term { [ 
                      quench_ratio_EM[T_EM_fct[],Norm[{d a}],Abs[CompZ[{is}]]]
            
                ]; In <<nc.omega>><<nc.powered>>_EM; Jacobian Jac_Vol_EM; }
                }
            }
            { Name Quench_Test;
                Value {
                Term { [ 
                      TestQuench[T_EM_fct[],Norm[{d a}],Abs[CompZ[{is}]]]
            
                ]; In <<nc.omega>><<nc.powered>>_EM; Jacobian Jac_Vol_EM; }
                }
            }
            {% if dm.quench_protection.quench_heaters.quench_prop_model == "Wilson" %}
            {% set post_cv_temp_EM = dm.magnet.solve.thermal.init_temperature %}
            {% else %}
            {% set post_cv_temp_EM = "Ts[T_EM_fct[],Norm[{d a}],Abs[CompZ[{is}]]]" %}
            {% endif %}
                { Name cv_EM;
                Value {
                {% for name, cond in dm.conductors.items() %}
                {% if loop.index not in ECLIQ_conductors %}
                Term { [
                {% if dm.quench_protection.quench_heaters.quench_prop_model == "Wilson" %}(Tc[T_EM_fct[],Norm[{d a}],Abs[CompZ[{is}]]]^4-<<dm.magnet.solve.thermal.init_temperature>>^4)/(4*<<dm.magnet.solve.thermal.init_temperature>>^3*(Tc[T_EM_fct[],Norm[{d a}],Abs[CompZ[{is}]]]-<<dm.magnet.solve.thermal.init_temperature>>))*{% endif %}
                  RuleOfMixtures[
                CFUN_CvCu_T[<<post_cv_temp_EM>>],
                CFUN_CvNb3Sn_T_B[<<post_cv_temp_EM>>, Norm[{d a}]],
                CFUN_CvG10_T[<<post_cv_temp_EM>>],
                CFUN_CvG10_T[<<post_cv_temp_EM>>]
                ]
                {
                f_stabilizer_<<name>>, 
                f_sc_<<name>>,
                f_inner_voids_<<name>>, 
                f_outer_voids_<<name>>
                }
                ]; In Omega_p_EM; Jacobian Jac_Vol_EM; }{% endif %}
                {% endfor %}
                }
            }
            { Name v_quench_EM;
                Value {
                Term { [ 
                      NZPV[T_EM_fct[],Norm[{d a}],Abs[CompZ[{is}]]]
            
                ]; In Omega_p_EM; Jacobian Jac_Vol_EM; }
                }
            }
            { Name Ts_EM;
                Value {
                Term { [ 
                      Ts[T_EM_fct[],Norm[{d a}],Abs[CompZ[{is}]]]
            
                ]; In Omega_p_EM; Jacobian Jac_Vol_EM; }
                }
            }
                { Name Tc_EM;
                Value {
                Term { [ 
                    Tc[T_EM_fct[],Norm[{d a}],Abs[CompZ[{is}]]]
            
                ]; In Omega_p_EM; Jacobian Jac_Vol_EM; }
                }
            }
            { Name Tcs_EM;
                Value {
                Term { [ 
                      Tcs[T_EM_fct[],Norm[{d a}],Abs[CompZ[{is}]]]
            
                ]; In Omega_p_EM; Jacobian Jac_Vol_EM; }
                }
            }
            { Name rho_EM ;
            Value {
                Term { [ resistivity[T_EM_fct[],Norm[{d a}],Abs[CompZ[{is}]]] ] ;
                In <<nc.omega>><<nc.powered>>_EM ; Jacobian Jac_Vol_EM ; }
            }
            }
          }
        }

      { Name Post_R_Quench_TH; NameOfFormulation Thermal_T; NameOfSystem Sys_The;
        Quantity {
                { Name R_Quench_TH;
                Value {
                Term { [ 
                      quench_ratio_TH[{T},Norm[{d a_after_projection}],I2TH_fct[]]
            
                ]; In <<nc.omega>><<nc.powered>>_TH; Jacobian Jac_Vol_TH; }
                }
            }
            {% if dm.quench_protection.quench_heaters.quench_prop_model == "Wilson" %}
            {% set post_cv_temp_TH = dm.magnet.solve.thermal.init_temperature %}
            {% else %}
            {% set post_cv_temp_TH = "Ts[{T},Norm[{d a_after_projection}],I2TH_fct[]]" %}
            {% endif %}
            { Name cv_TH;
                Value {
                {% for name, cond in dm.conductors.items() %}
                {% if loop.index not in ECLIQ_conductors %}
                Term { [ 
                {% if dm.quench_protection.quench_heaters.quench_prop_model == "Wilson" %}(Tc[{T},Norm[{d a_after_projection}],I2TH_fct[]]^4-<<dm.magnet.solve.thermal.init_temperature>>^4)/(4*<<dm.magnet.solve.thermal.init_temperature>>^3*(Tc[{T},Norm[{d a_after_projection}],I2TH_fct[]]-<<dm.magnet.solve.thermal.init_temperature>>))*{% endif %}
                                                        RuleOfMixtures[
                CFUN_CvCu_T[<<post_cv_temp_TH>>],
                CFUN_CvNb3Sn_T_B[<<post_cv_temp_TH>>,Norm[{d a_after_projection}] ],
                CFUN_CvG10_T[<<post_cv_temp_TH>>],
                CFUN_CvG10_T[<<post_cv_temp_TH>>]
                ]
                {
                f_stabilizer_<<name>>, 
                f_sc_<<name>>,
                f_inner_voids_<<name>>, 
                f_outer_voids_<<name>>
                }
                ]; In Omega_p_TH; Jacobian Jac_Vol_TH; }{% endif %}
                {% endfor %}
                }
            }
            { Name v_quench_TH;
                Value {
                Term { [ 
                      NZPV[{T},Norm[{d a_after_projection}],I2TH_fct[]]
            
                ]; In Omega_p_TH; Jacobian Jac_Vol_TH; }
                }
            }
                            { Name Ts_TH;
                Value {
                Term { [ 
                      Ts[{T},Norm[{d a_after_projection}],I2TH_fct[]]
            
                ]; In Omega_p_TH; Jacobian Jac_Vol_TH; }
                }
            }
            { Name Tc_TH;
                Value {
                Term { [ 
                      Tc[{T},Norm[{d a_after_projection}],I2TH_fct[]]
            
                ]; In Omega_p_TH; Jacobian Jac_Vol_EM; }
                }
            }
            { Name Tcs_TH;
                Value {
                Term { [ 
                      Tcs[{T},Norm[{d a_after_projection}],I2TH_fct[]]
            
                ]; In Omega_p_TH; Jacobian Jac_Vol_EM; }
                }
            }
            { Name rho_TH ;
            Value {
                Term { [ resistivity[{T}, Norm[{d a_after_projection}],I2TH_fct[]] ] ;
                In <<nc.omega>><<nc.powered>>_TH ; Jacobian Jac_Vol_TH ; }
            }
            }
          }
        }
        {% endif %}
    {% endif %}

    {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Th_Mag_sta' %}
    {Name GetI2TH; NameOfFormulation {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' %}Magnetodynamics_a_2D{% else %}Magnetostatics_a_2D{% endif %}; NameOfSystem {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' %}Sys_Mag_dyn{% else %}Sys_Mag_static{% endif %};
        PostQuantity{
            { Name I2TH ;
            Value {
                Integral { [ {is}/area_fct[]] ;
                In <<nc.omega>><<nc.powered>>_EM ; Jacobian Jac_Vol_EM ; Integration Int_EM ; }
            }
            }
        }
    }
    {% if SIM_MODE == 'Th_Mag' %}
        {Name GetI2TH_sta; NameOfFormulation Magnetostatics_a_2D; NameOfSystem Sys_Mag_static;
        PostQuantity{
            { Name I2TH ;
            Value {
                Integral { [ {is}/area_fct[]] ;
                In <<nc.omega>><<nc.powered>>_EM ; Jacobian Jac_Vol_EM ; Integration Int_EM ; }
            }
            }
        }
    }
    {% endif %}
    {% endif %}

    {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Th_Mag_sta' %}
    { Name Thermal_T ; NameOfFormulation Thermal_T ; NameOfSystem Sys_The ;
        PostQuantity {
        // Maximum temperature in bare part from register 1 (saved in post-operation by StoreMaxInRegister)
        {% if 'collar' in areas_to_build['TH'] %}
            { Name Tmax_col; Value{Term{ Type Global; [#1]; In <<nc.omega>><<nc.collar>>_TH;}}}
        {% endif %}
        
            { Name T_init_col; Value{Term{ Type Global; [<<dm.magnet.solve.thermal.init_temperature>>];}}}
        
            { Name Tmax;     Value{Term{ Type Global; [#1]; In <<nc.omega>>_TH;}}}
        // Temperature
            { Name T ;
                Value {
                Local { [ {T} ] ;
                    In <<nc.omega>>_TH ; Jacobian Jac_Vol_TH ; }
                }
            }
        {% if SIM_MODE == 'Th_Mag_sta' %}
            { Name jOverJc ;
                Value {
                Term { [ {% if dm.circuit.field_circuit %}I2TH_fct[]{% else %}i_fct[]{% endif %}/area_fct[] * 1/(criticalCurrentDensity[{T}, Norm[{d a_after_projection}]] + 1) ] ;
                    In <<nc.omega>><<nc.conducting>>_TH ; Jacobian Jac_Vol_TH ; } // area_fct[] is used on the thermal domain
                }
            }
        {% endif%}
        // Temperature average as integral quantity
            { Name T_avg ;
                Value {
                Integral {  [ {T} / area_fct[] ] ;
                    In Region[ {<<nc.omega>><<nc.powered>>_TH{% for area in areas_to_build['TH'] %}, <<nc.omega>><<nc[area]>>_TH{% endfor %}{% if dm.magnet.geometry.thermal.with_wedges %}, <<nc.omega>><<nc.induced>>_TH{% endif %} } ] ; Jacobian Jac_Vol_TH ; Integration Int_TH; }

                {% if not dm.magnet.geometry.thermal.use_TSA %}
                Integral {  [ {T} / area_fct[] ] ;
                    In <<nc.omega>><<nc.insulator>>_TH ; Jacobian Jac_Vol_TH ; Integration Int_TH; }
                {% endif %}
                }
            }
            { Name b_thermal ;
                Value {
                Local {  [{d a_after_projection}] ;
                    In <<nc.omega>>_noninsulation_areas_TH; Jacobian Jac_Vol_TH ; }
                }
            }

            { Name b_thermal_Gaussian_points ;
                Value {
                Local {  [GetVariable[ElementNum[], QuadraturePointIndex[]]{$b_before_projection}] ;
                    In <<nc.omega>>_noninsulation_areas_TH; Jacobian Jac_Vol_TH ; }
                }
            }

            { Name rho ;
            Value {
                Term { [ resistivity[{T}, Norm[{d a_after_projection}],I2TH_fct[]] ] ;
                In <<nc.omega>><<nc.powered>>_TH ; Jacobian Jac_Vol_TH ; }
            }
            }
            { Name az_thermal ; 
                Value {
                Term { [CompZ[{a_after_projection}] ]; In <<nc.omega>>_noninsulation_areas_TH; Jacobian Jac_Vol_TH; }
            }
            }
        }
    }

        {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or   SIM_MODE == 'Th_Mag_sta' %}
    { Name post_projection; NameOfFormulation Projection_EM_to_TH; NameOfSystem sys_Mag_projection;
        PostQuantity {
            { Name b_before_projection ;
                Value {
                Term {  [Norm[{d a_before_projection}]] ;
                    In <<nc.omega>><<nc.powered>>_TH ; Jacobian Jac_Vol_TH ; }
                }
            }
            { Name b_after_projection ;
                Value {
                Term {  [{d a_after_projection}] ;
                    In <<nc.omega>><<nc.powered>>_TH ; Jacobian Jac_Vol_TH ; }
                }
            }
        }
    }
        {% endif %}
    {% endif %}
}

{% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Th_Mag_sta' %}
    PostOperation PrintMaxTemp UsingPost Thermal_T {
        // Get maximum in bare region and store in register 1
        Print[ T, OnElementsOf <<nc.omega>>_TH, StoreMaxInRegister 1, Format Table,
            LastTimeStepOnly 1, SendToServer "No"] ;
        Print[ Tmax, OnRegion Region[<<rm_TH.powered['r1_a1'].vol.numbers[0]>>], File "Tmax.txt", Format TimeTable, LastTimeStepOnly 1, AppendToExistingFile 1, SendToServer "No"]; // Pick a random Region 
    }
    {% if 'collar' in areas_to_build['TH'] %}
    PostOperation PrintMaxTemp_col UsingPost Thermal_T {
        // Get maximum in collar region and store in register 1
        Print[ T, OnElementsOf <<nc.omega>><<nc.collar>>_TH , StoreMaxInRegister 1, Format TimeTable,
            LastTimeStepOnly 1, SendToServer "No"] ; 
        Print[ Tmax_col, OnRegion <<nc.omega>><<nc.collar>>_TH ,
          File "Tmax_col.txt", Format Table, LastTimeStepOnly 1, AppendToExistingFile 1, SendToServer "No"];
    }
    {% endif %}
{% endif %}

PostOperation {
    { Name Dummy; NameOfPostProcessing {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Th_Mag_sta' %} Thermal_T {% elif SIM_MODE == 'Mag_dyn' or SIM_MODE == 'Mag_dyn_0' %} MagDyn_a_2D {% else %} MagSta_a_2D {% endif %};
        Operation { }
    }
    {% if dm.circuit.field_circuit %}
    <<cc_macros2.postOP_FCC(nc,rm_EM,dm,flag_active,regions_CC,init_ht,SIM_MODE,ESC_dict,ECLIQ_dict)>>
    {% endif %}

    {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Mag_dyn' or SIM_MODE == 'Mag_dyn_0' %}
    { Name Map_a; NameOfPostProcessing MagDyn_a_2D;
        Operation {
        {% for var_name, vol_name in zip(dm.magnet.postproc.electromagnetics.variables, dm.magnet.postproc.electromagnetics.volumes) %}
            Print[ <<var_name>>, OnElementsOf <<vol_name>>_EM, File "<<var_name>>_<<vol_name>>.pos"] ;
        {% endfor %}
            //Print[ E_mag, OnGlobal , File "E_mag.csv", Format Table, Comma, SendToServer "No", AppendToExistingFile 1] ;
	        //Print [ b, OnLine {{List[{0,0,0}]}{List[{<<rm_EM.air_far_field.vol.radius_out>>,0,0}]}} {1000}, Format SimpleTable, File "Center_line.csv"];
        }
    }


    {% if (dm.quench_protection.quench_heaters.quench_propagation == "2Dx1D" or dm.quench_protection.e_cliq.quench_propagation == "2Dx1D") and dm.magnet.solve.thermal.solve_type%}
        { Name Map_R_quench; NameOfPostProcessing Post_R_Quench_EM;
              Operation {
            // Print[ R_Quench_EM, OnElementsOf Omega_p_EM , File "QR_EM.csv", Format Table, Comma, SendToServer "No", AppendToExistingFile 1] ;
            Print[ Quench_Test, OnElementsOf Omega_p_EM , File "Test_Quench.pos", SendToServer "No", LastTimeStepOnly 1, AppendToExistingFile 1] ;
            Print[ R_Quench_EM, OnElementsOf Omega_p_EM , File "QR_EM.pos", SendToServer "No", LastTimeStepOnly 1, AppendToExistingFile 1] ;
            Print[ Ts_EM, OnElementsOf Omega_p_EM , File "Ts_EM.pos", SendToServer "No", LastTimeStepOnly 1, AppendToExistingFile 1] ;
            Print[ Tc_EM, OnElementsOf Omega_p_EM , File "Tc_EM.pos", SendToServer "No", LastTimeStepOnly 1, AppendToExistingFile 1] ;
            Print[ Tcs_EM, OnElementsOf Omega_p_EM , File "Tcs_EM.pos", SendToServer "No", LastTimeStepOnly 1, AppendToExistingFile 1] ;
            Print[ v_quench_EM, OnElementsOf Omega_p_EM , File "v_quench_EM.pos", SendToServer "No", LastTimeStepOnly 1, AppendToExistingFile 1] ;
            Print[ cv_EM, OnElementsOf Omega_p_EM , File "cv_EM.pos", SendToServer "No", LastTimeStepOnly 1, AppendToExistingFile 1] ;
            Print[ rho_EM, OnElementsOf Omega_p_EM , File "rho_EM.pos", SendToServer "No", LastTimeStepOnly 1, AppendToExistingFile 1] ;
          
              }
            }

    { Name Map_R_quench_TH; NameOfPostProcessing Post_R_Quench_TH;
              Operation {
            Print[ R_Quench_TH, OnElementsOf Omega_p_TH , File "QR_TH.pos", SendToServer "No", LastTimeStepOnly 1, AppendToExistingFile 1] ;
            Print[ Ts_TH, OnElementsOf Omega_p_TH , File "Ts_TH.pos", SendToServer "No", LastTimeStepOnly 1, AppendToExistingFile 1] ;
            Print[ Tc_TH, OnElementsOf Omega_p_TH , File "Tc_TH.pos", SendToServer "No", LastTimeStepOnly 1, AppendToExistingFile 1] ;
            Print[ Tcs_TH, OnElementsOf Omega_p_TH , File "Tcs_TH.pos", SendToServer "No", LastTimeStepOnly 1, AppendToExistingFile 1] ;
            Print[ v_quench_TH, OnElementsOf Omega_p_TH , File "v_quench_TH.pos", SendToServer "No", LastTimeStepOnly 1, AppendToExistingFile 1] ;
            Print[ cv_TH, OnElementsOf Omega_p_TH , File "cv_TH.pos", SendToServer "No", LastTimeStepOnly 1, AppendToExistingFile 1] ;
            Print[ rho_TH, OnElementsOf Omega_p_TH , File "rho_TH.pos", SendToServer "No", LastTimeStepOnly 1, AppendToExistingFile 1] ;
              
              }
            }
    {% endif %}
    { Name conv; NameOfPostProcessing MagDyn_a_2D;
        Operation {
            Print[ E_mag, OnGlobal] ;
        }
    }
    {% if dm.circuit.field_circuit %}
    { Name conv2; NameOfPostProcessing MagDyn_a_2D;
        Operation {
            Print[ I_, OnRegion Omega_PS_R_c_r] ;
            {% if flag_active['ECLIQ'] %}
            Print[ I_, OnRegion Omega_ECLIQ_R_leads_1] ;
            Print[ I_, OnRegion Omega_ECLIQ_R_leads_2] ;
            Print[ I_, OnRegion Omega_ECLIQ_R_leads_3] ;
            Print[ I_, OnRegion Omega_ECLIQ_R_leads_4] ;
            {% endif %}
            // Print[ I_, OnRegion Omega_PS_R_3] ;
            // Print[ I_, OnRegion Omega_PS_R_1] ;
        }
      }
        {% endif %} 
    {% endif %}

    {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_sta' or SIM_MODE == 'Mag_sta' or SIM_MODE == 'Mag_dyn' %}
    { Name Map_a_sta; NameOfPostProcessing MagSta_a_2D;
        Operation {
        {% for var_name, vol_name in zip(dm.magnet.postproc.electromagnetics.variables, dm.magnet.postproc.electromagnetics.volumes) %}
            Print[ <<var_name>>, OnElementsOf <<vol_name>>_EM, File "<<var_name>>_<<vol_name>>.pos"] ;
        {% endfor %}
	        //Print [ b, OnLine {{List[{0,0,0}]}{List[{<<rm_EM.air_far_field.vol.radius_out>>,0,0}]}} {1000}, Format SimpleTable, File "Center_line.csv"];
        }
    }
    {% if dm.circuit.field_circuit and (SIM_MODE == 'Mag_sta' or SIM_MODE == 'Th_Mag_sta' or SIM_MODE == 'Th_Mag' or SIM_MODE == 'Mag_dyn' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Mag_dyn_0' ) %}
    { Name conv2_sta; NameOfPostProcessing MagSta_a_2D;
        Operation {
            Print[ I_, OnRegion Omega_PS_R_c_r] ;
            // Print[ I_, OnRegion Omega_PS_R_3] ;
            // Print[ I_, OnRegion Omega_PS_R_1] ;
        }
      }
        {% endif %} 
    {% endif %}


    {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' or SIM_MODE == 'Th_Mag_sta' %}
    { Name b_thermal; NameOfPostProcessing Thermal_T;
        Operation {
        Print[ b_thermal, OnElementsOf <<nc.omega>>_noninsulation_areas_TH, File "b_thermal.pos"] ;
        }
    }
        {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Th_Mag_0' %}
    { Name b_after_projection_pos; NameOfPostProcessing post_projection;
        Operation {
        Print[ b_after_projection, OnElementsOf <<nc.omega>><<nc.powered>>_TH, File "b_after_projection.pos"] ;
        }
    }
        {% endif %}

    { Name Map_T; NameOfPostProcessing Thermal_T;
        {% if dm.magnet.postproc.thermal.output_time_steps_pos > 1 %}
            {%  if dm.magnet.solve.thermal.solve_type and dm.magnet.solve.electromagnetics.solve_type == 'transient' %}
                {% set resample_step = (dm.magnet.solve.time_stepping.final_time - dm.magnet.solve.time_stepping.initial_time)/dm.magnet.postproc.thermal.output_time_steps_pos %}
                {% set last_time_step_only = 0 %}
        ResampleTime[<<dm.magnet.solve.time_stepping.initial_time>>, <<dm.magnet.solve.time_stepping.final_time>>, <<resample_step>>];
            {%  else %}
                {% set resample_step = (dm.magnet.solve.thermal.time_stepping.final_time - dm.magnet.solve.thermal.time_stepping.initial_time)/dm.magnet.postproc.thermal.output_time_steps_pos %}
                {% set last_time_step_only = 0 %}
        ResampleTime[<<dm.magnet.solve.thermal.time_stepping.initial_time>>, <<dm.magnet.solve.thermal.time_stepping.final_time>>, <<resample_step>>];
            {%  endif %}
        {% elif (dm.magnet.postproc.thermal.output_time_steps_pos == 1 and not dm.magnet.postproc.thermal.save_pos_at_the_end) %}
            {% set last_time_step_only = 1 %}
        {% else %}
            {% set last_time_step_only = 0 %}
        {% endif %}
        Operation {
        {% for var_name, vol_name in zip(dm.magnet.postproc.thermal.variables, dm.magnet.postproc.thermal.volumes) %}
            Print[ <<var_name>>, OnElementsOf <<vol_name>>_TH, File "<<var_name>>_<<vol_name>>.pos", SendToServer "No", LastTimeStepOnly <<last_time_step_only>>, AppendToExistingFile <<last_time_step_only>> ] ;
        {% endfor %}
            //Print[ T, OnElementsOf <<nc.omega>>_TH, File "T_<<nc.omega>>.pos", SendToServer "No", LastTimeStepOnly <<last_time_step_only>>, AppendToExistingFile <<last_time_step_only>> ] ;
            //Print[ JoverJc, OnElementsOf <<nc.omega>><<nc.powered>>_TH, File "JoverJc_<<nc.omega>><<nc.powered>>.pos", SendToServer "No", LastTimeStepOnly <<last_time_step_only>>, AppendToExistingFile <<last_time_step_only>>, AtGaussPoints 4, Depth 0 ] ;
            //Print[ rho, OnElementsOf <<nc.omega>><<nc.powered>>_TH, File "rho_<<nc.omega>><<nc.powered>>.pos", SendToServer "No", LastTimeStepOnly <<last_time_step_only>>, AppendToExistingFile <<last_time_step_only>> ] ;
        }
    }

    { Name T_avg; NameOfPostProcessing Thermal_T;
        {% if dm.magnet.postproc.thermal.output_time_steps_txt > 1 %}
            {%  if dm.magnet.solve.thermal.solve_type and dm.magnet.solve.electromagnetics.solve_type == 'transient' %}
                {% set resample_step = (dm.magnet.solve.time_stepping.final_time - dm.magnet.solve.time_stepping.initial_time)/dm.magnet.postproc.thermal.output_time_steps_pos %}
                {% set last_time_step_only = 0 %}
        ResampleTime[<<dm.magnet.solve.time_stepping.initial_time>>, <<dm.magnet.solve.time_stepping.final_time>>, <<resample_step>>];
            {%  else %}
                {% set resample_step = (dm.magnet.solve.thermal.time_stepping.final_time - dm.magnet.solve.thermal.time_stepping.initial_time)/dm.magnet.postproc.thermal.output_time_steps_pos %}
                {% set last_time_step_only = 0 %}
        ResampleTime[<<dm.magnet.solve.thermal.time_stepping.initial_time>>, <<dm.magnet.solve.thermal.time_stepping.final_time>>, <<resample_step>>];
            {%  endif %}
        {% elif (dm.magnet.postproc.thermal.output_time_steps_txt == 1 and not dm.magnet.postproc.thermal.save_txt_at_the_end) %}
            {% set last_time_step_only = 1 %}
        {% else %}
            {% set last_time_step_only = 0 %}
        {% endif %}
        Operation {
            // writes pairs of time step and average temperature to file, one line for each time step
        {% for idx, half_turn in enumerate(rm_TH.powered['r1_a1'].vol.numbers + rm_TH.powered['r2_a1'].vol.numbers + rm_TH.powered['r1_a2'].vol.numbers + rm_TH.powered['r2_a2'].vol.numbers ) %}
            Print[ T_avg[Region[<<half_turn>>]], OnGlobal, File "T_avg/T_avg_<<idx>>.txt", Format Table, SendToServer "No", LastTimeStepOnly <<last_time_step_only>>, AppendToExistingFile <<last_time_step_only>>, StoreInVariable $T_a_<<idx>>] ;
        {% endfor %}
        {% if dm.magnet.geometry.thermal.with_wedges %}
            {% set ht_max=len(rm_TH.powered['r1_a1'].vol.numbers + rm_TH.powered['r2_a1'].vol.numbers + rm_TH.powered['r1_a2'].vol.numbers + rm_TH.powered['r2_a2'].vol.numbers)%}
            {% for idx, phy_elem in enumerate( rm_TH.induced['r1_a1'].vol.numbers + rm_TH.induced['r2_a1'].vol.numbers + rm_TH.induced['r1_a2'].vol.numbers + rm_TH.induced['r2_a2'].vol.numbers) %}
            Print[ T_avg[Region[<<phy_elem>>]], OnGlobal, File "T_avg/T_avg_<<idx+ht_max>>.txt", Format Table, SendToServer "No", LastTimeStepOnly <<last_time_step_only>>, AppendToExistingFile <<last_time_step_only>>, StoreInVariable $T_a_<<idx+ht_max>>] ;
            {% endfor %}
        {% endif %}
        }
    }
        {% if dm.magnet.geometry.thermal.with_wedges %}
     { Name T_avg_init; NameOfPostProcessing Thermal_T; // for the initial temperature
        {% set ht_max=len(rm_TH.powered['r1_a1'].vol.numbers + rm_TH.powered['r2_a1'].vol.numbers + rm_TH.powered['r1_a2'].vol.numbers + rm_TH.powered['r2_a2'].vol.numbers)%}
        {% for idx, phy_elem in enumerate( rm_TH.induced['r1_a1'].vol.numbers + rm_TH.induced['r2_a1'].vol.numbers + rm_TH.induced['r1_a2'].vol.numbers + rm_TH.induced['r2_a2'].vol.numbers) %}
        Operation{
            Print[ T_init_col, OnGlobal, File "T_avg/T_avg_<<idx+ht_max>>.txt", Format Table, SendToServer "No", LastTimeStepOnly 1, AppendToExistingFile 1, StoreInVariable $T_a_<<idx+ht_max>>] ;
        }
        {% endfor %}
    }
    {% endif %}
    {% if USE_THERMAL_PROJECTION %}
    { Name T_avg_collar; NameOfPostProcessing Thermal_T;
        Operation {
            Print[ T_avg[<<nc.omega>><<nc.collar>>_TH],  OnGlobal, File "T_av_col.txt", Format Table, SendToServer "No", LastTimeStepOnly 1, AppendToExistingFile 1, StoreInVariable $T_a_col] ;            
        }
    }
    { Name T_avg_collar_init; NameOfPostProcessing Thermal_T;  // for the initial temperature
        Operation {
            Print[ T_init_col,  OnGlobal, File "T_av_col.txt", Format Table, SendToServer "No", LastTimeStepOnly 1, AppendToExistingFile 1, StoreInVariable $T_a_col] ; //DEBUG why is this always 0 ?
        }
    }
    {% endif %}

    { Name GetI2TH; NameOfPostProcessing GetI2TH;
        Operation { 
            Print[ I2TH[Region[<<pol_['right']>>]], OnGlobal, File "I2TH/I2TH_Mag_r.txt", Format Table, SendToServer "No", LastTimeStepOnly 0, AppendToExistingFile 0, StoreInVariable $I2TH_1] ;
            Print[ I2TH[Region[<<pol_['left']>>]], OnGlobal, File "I2TH/I2TH_Mag_l.txt", Format Table, SendToServer "No", LastTimeStepOnly 0, AppendToExistingFile 0, StoreInVariable $I2TH_2] ;
            {% for i,ht in enumerate(aux.half_turns.ADD_COILS) %}
            Print[ I2TH[Region[<<'ht'~ht~'_EM'>>]], OnGlobal, File "I2TH/I2TH_.txt", Format Table, SendToServer "No", LastTimeStepOnly 0, AppendToExistingFile 0, StoreInVariable $I2TH_<<i+3>>] ;
            {% endfor %}
      
      
       }
      }
      {% if SIM_MODE == 'Th_Mag' %}
          { Name GetI2TH_sta; NameOfPostProcessing GetI2TH_sta;
        Operation { 
            Print[ I2TH[Region[<<pol_['right']>>]], OnGlobal, File "I2TH/I2TH_r.txt", Format Table, SendToServer "No", LastTimeStepOnly 0, AppendToExistingFile 0, StoreInVariable $I2TH_1] ;
            Print[ I2TH[Region[<<pol_['left']>>]], OnGlobal, File "I2TH/I2TH_l.txt", Format Table, SendToServer "No", LastTimeStepOnly 0, AppendToExistingFile 0, StoreInVariable $I2TH_2] ;
            {% for i,ht in enumerate(aux.half_turns.ADD_COILS) %}
            Print[ I2TH[Region[<<'ht'~ht~'_EM'>>]], OnGlobal, File "I2TH/I2TH_.txt", Format Table, SendToServer "No", LastTimeStepOnly 0, AppendToExistingFile 0, StoreInVariable $I2TH_<<i+3>>] ;
            {% endfor %}
      
      
       }
      }
      {% endif %}
    {% endif %}
}