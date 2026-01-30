
// Resistivities for magnetostatic simulations:
{% macro MATERIAL_Resistivity_Copper_T_B(RRR="None", RRRRefTemp="None", T="None", BMagnitude="Norm[$1]") -%}
CFUN_rhoCu_T_B[<<T>>, <<BMagnitude>>]{<<RRR>>}
{%- endmacro %}
{% macro MATERIAL_Resistivity_Copper_T(RRR="None", RRRRefTemp="None", T="$1", BMagnitude="5") -%}
CFUN_rhoCu_T[<<T>>]{<<BMagnitude>>, <<RRR>>}
{%- endmacro %}

{% macro MATERIAL_Resistivity_Hastelloy_T(RRR="None", RRRRefTemp="None", T="$1", BMagnitude="5") -%}
CFUN_rhoHast_T[<<T>>]
{%- endmacro %}

{% macro MATERIAL_Resistivity_Silver_T_B(RRR="None", RRRRefTemp="None", T="None", BMagnitude="Norm[$1]") -%}
CFUN_rhoAg_T_B[<<T>>, <<BMagnitude>>]{<<RRR>>, <<RRRRefTemp>>}
{%- endmacro %}
{% macro MATERIAL_Resistivity_Silver_T(RRR="None", RRRRefTemp="None", T="$1", BMagnitude="5") -%}
CFUN_rhoAg_T[<<T>>]{<<BMagnitude>>, <<RRR>>, <<RRRRefTemp>>}
{%- endmacro %}

{% macro MATERIAL_Resistivity_Indium_T(RRR="None", RRRRefTemp="None", T="$1", BMagnitude="5") -%}
CFUN_rhoIn_T[<<T>>]
{%- endmacro %}

{% macro MATERIAL_Resistivity_SSteel_T(RRR="None", RRRRefTemp="None", T="$1", BMagnitude="5") -%}
CFUN_rhoSS_T[<<T>>]
{%- endmacro %}
// AUX Function
{%- macro increment(dct, key, inc=1)-%}
{%- do dct.update({key: dct[key] + inc}) -%}
{%- endmacro -%}
//Regions
{%- macro cliq_regions(dm,CLIQ_dict,aux) %}
{%  set counter = {"counter1": 0} %}
{%  set CLIQ_groups = [] -%}

{%-  set group_to_coil_section = dm.magnet.solve.coil_windings.group_to_coil_section %}
{%  set unique_coils = group_to_coil_section | unique %}
{%  set max_coil = group_to_coil_section | max %}
{%  set elec_order = dm.magnet.solve.coil_windings.electrical_pairs.overwrite_electrical_order %}
{%  set group_together = dm.magnet.solve.coil_windings.electrical_pairs.group_together %}
{%  set helper = {"first_group": none, "last_group": none} %}

{%-  set CLIQ_leads = [] %}
{%  set CLIQ_groups = [] %}
{%  set CLIQ_Units = 0 -%}

{#-  Iterate over unique coil numbers greater than 1 #}
{%  for coil in unique_coils if coil > 1 %}
{%    set coil_groups = [] %}
{%-    for group in group_to_coil_section %}
{%      if group == coil %}
{%        do coil_groups.append(loop.index) %} {# Use loop.index0 for zero-based index #}
{%      endif %}
{%    endfor -%}

{#-   Find the first and last groups in electrical order #}
{%    do helper.update({"first_group": none, "last_group": none}) %}
{%    for pair in group_together %}
{%      if pair[0] in coil_groups or pair[1] in coil_groups %}
{%        if helper["first_group"] is none %}
{%          do helper.update({"first_group": pair[0] if pair[0] in coil_groups else pair[1]}) %}
{%        endif %}
{%        do helper.update({"last_group": pair[1] if pair[1] in coil_groups else pair[0]}) %}
{%      endif %}
{%    endfor %}

{#-  Get the first and last leads for the current coil based on electrical order #}
{%    set first_lead = aux.half_turns.ht[helper["first_group"]][0] %}
{%    set last_lead = aux.half_turns.ht[helper["last_group"]][-1] -%}


{#-  Determine the indices of the leads in elec_order #}
{%    set first_lead_index = elec_order.index(first_lead) %}
{%    set last_lead_index = elec_order.index(last_lead) %}

{#-  Append the indices to the appropriate list -#}
{%    do CLIQ_leads.append(first_lead_index) %}
{%    do CLIQ_leads.append(last_lead_index) %}
{%-    do CLIQ_groups.append(coil_groups) -%}
<< increment(counter, "counter1") >>
{%-  endfor -%}

{%-  set CLIQ_Units = counter["counter1"] -%}

{#-  Update CLIQ_dict with the required information #}
{%  do CLIQ_dict.update({
    "Units": CLIQ_Units,
    "groups": CLIQ_groups,
    "leads": CLIQ_leads
    }) %}
{%- endmacro -%}

{%- macro esc_regions(dm,ESC_dict,aux) %}
{%  set counter = {"counter1": 0} %}
{%  set ESC_groups = [] -%}
{%-  set ESC_leads = [] %}
{%  set ESC_groups = [] %}
{%  set ESC_Units = 0 -%}

{%-  set group_to_coil_section = dm.magnet.solve.coil_windings.group_to_coil_section %}
{%  set group_together = dm.magnet.solve.coil_windings.electrical_pairs.group_together %}

{%  set unique_coils = group_to_coil_section | unique %}
{%  set max_coil = group_to_coil_section | max %}
{%  set elec_order = aux.half_turns.ADD_COILS %}

{%  set helper = {"first_group": none, "last_group": none} %}

{#-  Iterate over unique coil numbers greater than 1 #}
{%  for coil in unique_coils if coil > 1 %}
{%    set coil_groups = [] %}
{%-    for group in group_to_coil_section %}
{%      if group == coil %}
{%        do coil_groups.append(loop.index) %} {# Use loop.index0 for zero-based index #}
{%      endif %}
{%    endfor -%}

{#-   Find the first and last groups in electrical order #}
{%    do helper.update({"first_group": none, "last_group": none}) %}
{%    for pair in group_together %}
{%      if pair[0] in coil_groups or pair[1] in coil_groups %}
{%        if helper["first_group"] is none %}
{%          do helper.update({"first_group": pair[0] if pair[0] in coil_groups else pair[1]}) %}
{%        endif %}
{%        do helper.update({"last_group": pair[1] if pair[1] in coil_groups else pair[0]}) %}
{%      endif %}
{%    endfor %}

{#-  Get the first and last leads for the current coil based on electrical order #}
{%    set first_lead = aux.half_turns.ht[helper["first_group"]][0] %}
{%    set last_lead = aux.half_turns.ht[helper["last_group"]][-1] -%}


{#-  Determine the indices of the leads in elec_order #}
{%    set first_lead_index = elec_order.index(first_lead) %}
{%    set last_lead_index = elec_order.index(last_lead) %}

{#-  Append the indices to the appropriate list -#}
{%    do ESC_leads.append(first_lead_index) %}
{%    do ESC_leads.append(last_lead_index) %}
{%-    do ESC_groups.append(coil_groups) -%}
<< increment(counter, "counter1") >>
{%-  endfor -%}

{%-  set ESC_Units = counter["counter1"] -%}



{#-  Update ESC_dict with the required information #}
{%  do ESC_dict.update({
    "Units": ESC_Units,
    "groups": ESC_groups,
    "leads": ESC_leads
    }) %}
{%- endmacro -%}

{%- macro ecliq_regions(dm,ECLIQ_dict,aux) %}
{%  set counter = {"counter1": 0} %}
{%  set ECLIQ_groups = [] -%}

{%-  set group_to_coil_section = dm.magnet.solve.coil_windings.group_to_coil_section %}
{%  set unique_coils = group_to_coil_section | unique %}
{%  set max_coil = group_to_coil_section | max %}
{%  set elec_order = aux.half_turns.ADD_COILS %}
{%  set group_together = dm.magnet.solve.coil_windings.electrical_pairs.group_together %}
{%  set helper = {"first_group": none, "last_group": none} %}

{%-  set ECLIQ_leads = [] %}
{%  set ECLIQ_groups = [] %}
{%  set ECLIQ_Units = 0 -%}

{#-  Iterate over unique coil numbers greater than 1 #}
{%  for coil in unique_coils if coil > 1 %}
{%    set coil_groups = [] %}
{%-    for group in group_to_coil_section %}
{%      if group == coil %}
{%        do coil_groups.append(loop.index) %} {# Use loop.index0 for zero-based index #}
{%      endif %}
{%    endfor -%}

{#-   Find the first and last groups in electrical order #}
{%    do helper.update({"first_group": none, "last_group": none}) %}
{%    for pair in group_together %}
{%      if pair[0] in coil_groups or pair[1] in coil_groups %}
{%        if helper["first_group"] is none %}
{%          do helper.update({"first_group": pair[0] if pair[0] in coil_groups else pair[1]}) %}
{%        endif %}
{%        do helper.update({"last_group": pair[1] if pair[1] in coil_groups else pair[0]}) %}
{%      endif %}
{%    endfor %}

{#-  Get the first and last leads for the current coil based on electrical order #}
{%    set first_lead = aux.half_turns.ht[helper["first_group"]][0] %}
{%    set last_lead = aux.half_turns.ht[helper["last_group"]][-1] -%}


{#-  Determine the indices of the leads in elec_order #}
{%    set first_lead_index = elec_order.index(first_lead) %}
{%    set last_lead_index = elec_order.index(last_lead) %}

{#-  Append the indices to the appropriate list -#}
{%    do ECLIQ_leads.append(first_lead_index) %}
{%    do ECLIQ_leads.append(last_lead_index) %}
{%-    do ECLIQ_groups.append(coil_groups) -%}
<< increment(counter, "counter1") >>
{%-  endfor -%}

{%-  set ECLIQ_Units = counter["counter1"] -%}



{#-  Update ECLIQ_dict with the required information #}
{%  do ECLIQ_dict.update({
    "Units": ECLIQ_Units,
    "groups": ECLIQ_groups,
    "leads": ECLIQ_leads
    }) %}
{%- endmacro -%}

{%- macro generate_polarity_groups(dm, rm_EM,aux,pol_) -%}
{%  set polarities = dm.magnet.solve.coil_windings.polarities_in_group -%}
{%  set Omega_p_EM_r = [] -%}
{%  set Omega_p_EM_l = [] -%}

{#- Iterate over the indices of polarities and assign regions to the appropriate group -#}
{% if len(polarities)>0 %}
{%  for i in range(polarities | length) -%}
{%    set polarity = polarities[i] -%}
{%    set half_turns = aux.half_turns.ht[i+1] -%}
{%    for half_turn in half_turns -%}
{%      if polarity == 1 -%}
{%        do Omega_p_EM_r.append('ht' ~ half_turn ~ '_EM') -%}
{%      elif polarity == -1 -%}
{%        do Omega_p_EM_l.append('ht' ~ half_turn ~ '_EM') -%}
{%      endif -%}
{%    endfor -%}
{%  endfor -%}
{% do pol_.update({"first": dm.magnet.solve.coil_windings.polarities_in_group[dm.magnet.solve.coil_windings.electrical_pairs.group_together[0][0]-1]}) %}
{% else %}
{#- Fallback mechanism when dm.magnet.solve.coil_windings is not available -#}
{% for name, current in zip(
    rm_EM.powered['r1_a1'].vol.names + rm_EM.powered['r1_a2'].vol.names + rm_EM.powered['r2_a1'].vol.names + rm_EM.powered['r2_a2'].vol.names,
    rm_EM.powered['r1_a1'].vol.currents + rm_EM.powered['r1_a2'].vol.currents + rm_EM.powered['r2_a1'].vol.currents + rm_EM.powered['r2_a2'].vol.currents
) %}
    {% if current > 0 %}
        {% do Omega_p_EM_r.append(name) %}
    {% elif current < 0 %}
        {% do Omega_p_EM_l.append(name) %}
    {% endif %}
{% endfor %}
{% endif %}
{% do pol_.update({"right": Omega_p_EM_r[0]}) %}
{%  if len(Omega_p_EM_l)>0%}
{% do pol_.update({"left": Omega_p_EM_l[0]}) %}
{% else %}
{% do pol_.update({"left": Omega_p_EM_r[1]}) %}
{% endif %}

{#- Generate the regions dynamically #}
  Omega_p_EM_r = Region[{ << Omega_p_EM_r | join(', ') >> }];
  Omega_p_EM_l = Region[{ << Omega_p_EM_l | join(', ') >> }];
{% endmacro%}

{%- macro generate_polarity_groups_TH(dm,aux,rm_EM,rm_TH) -%}
{%  set polarities = dm.magnet.solve.coil_windings.polarities_in_group -%}
{%  set Omega_p_TH_r = [] -%}
{%  set Omega_p_TH_l = [] -%}

{#- Iterate over the indices of polarities and assign regions to the appropriate group -#}
{% if len(polarities)>0 %}
{%  for i in range(polarities | length) -%}
{%    set polarity = polarities[i] -%}
{%    set half_turns = aux.half_turns.ht[i+1] -%}
{%    for half_turn in half_turns -%}
{%      if polarity == 1 -%}
{%        do Omega_p_TH_r.append('ht' ~ half_turn ~ '_TH') -%}
{%      elif polarity == -1 -%}
{%        do Omega_p_TH_l.append('ht' ~ half_turn ~ '_TH') -%}
{%      endif -%}
{%    endfor -%}
{%  endfor -%}
{% else %}
{#- Fallback mechanism when dm.magnet.solve.coil_windings is not available -#}
{% for name, current in zip(
    rm_TH.powered['r1_a1'].vol.names + rm_TH.powered['r1_a2'].vol.names + rm_TH.powered['r2_a1'].vol.names + rm_TH.powered['r2_a2'].vol.names,
    rm_EM.powered['r1_a1'].vol.currents + rm_EM.powered['r1_a2'].vol.currents + rm_EM.powered['r2_a1'].vol.currents + rm_EM.powered['r2_a2'].vol.currents
) %}
    {% if current > 0 %}
        {% do Omega_p_TH_r.append(name) %}
    {% elif current < 0 %}
        {% do Omega_p_TH_l.append(name) %}
    {% endif %}
{% endfor %}
{% endif %}

{#- Generate the regions dynamically #}
  Omega_p_TH_r = Region[{ << Omega_p_TH_r | join(', ') >> }];
  Omega_p_TH_l = Region[{ << Omega_p_TH_l | join(', ') >> }];
{% endmacro %}

{# MAIN MACROS #}

{% macro regions_FCC(dm,rm_EM,flag_active,regions_CC,end_ht,CLIQ_dict,ECLIQ_dict,ESC_dict,CC_dict,aux) -%} 

{%- set N_ht = end_ht %}
{%  set magnet_reg_lim = aux.half_turns.max_reg %}
{%  set group_to_coil_section = dm.magnet.solve.coil_windings.group_to_coil_section %}
{%  set max_coil = group_to_coil_section | max -%}

{%- do flag_active.update({"ECLIQ": 0}) %}
{%  do flag_active.update({"CLIQ": 0}) %}
{%  do flag_active.update({"ESC": 0}) %}
{%  do flag_active.update({"EE": 0}) %}
  
{#-  Check if there are no quench protection mechanisms #}
{% set t_trigger_EE = [dm.quench_protection.energy_extraction.t_trigger, dm.quench_protection.energy_extraction.t_trigger_n] %}
{%  if (t_trigger_EE | max <= dm.magnet.solve.electromagnetics.time_stepping.final_time or t_trigger_EE | max <= dm.magnet.solve.thermal.time_stepping.final_time or t_trigger_EE | max <= dm.magnet.solve.time_stepping.final_time ) %}
{%    do flag_active.update({"EE": 1})%}
{%  endif%}
{%  if max_coil == 1 %}
{%    do flag_active.update({"CLIQ": 0, "ESC": 0}) %}
{%  else%}
{%    if max_coil >1 and (dm.quench_protection.cliq.t_trigger<dm.magnet.solve.electromagnetics.time_stepping.final_time or dm.quench_protection.cliq.t_trigger<dm.magnet.solve.thermal.time_stepping.final_time or dm.quench_protection.cliq.t_trigger<dm.magnet.solve.time_stepping.final_time) %}
{%      do flag_active.update({"CLIQ": 1}) %}
  <<cliq_regions(dm,CLIQ_dict,aux)>>
{%    endif%}
{%    if max_coil >1 and (dm.quench_protection.esc.t_trigger | max < dm.magnet.solve.electromagnetics.time_stepping.final_time or dm.quench_protection.esc.t_trigger | max < dm.magnet.solve.thermal.time_stepping.final_time or dm.quench_protection.esc.t_trigger | max < dm.magnet.solve.time_stepping.final_time) %}
{%      do flag_active.update({"ESC": 1}) %}
  <<esc_regions(dm,ESC_dict,aux)>>
{%    elif max_coil >1 and (dm.quench_protection.e_cliq.t_trigger | max < dm.magnet.solve.electromagnetics.time_stepping.final_time or dm.quench_protection.e_cliq.t_trigger | max < dm.magnet.solve.thermal.time_stepping.final_time or dm.quench_protection.e_cliq.t_trigger | max < dm.magnet.solve.time_stepping.final_time) %}
{%      do flag_active.update({"ECLIQ": 1}) %}
  <<ecliq_regions(dm,ECLIQ_dict,aux)>>
{#      do ECLIQ_dict.update({"Units": len(dm.quench_protection.e_cliq.t_trigger)}) #}
{%    endif%}
{%-  endif -%}

{#- Initialize dictionaries for each region type #}
{%  set inductance_regions = {"PS": [], "circuit": [], "EE": [], "ESC": [], "CLIQ": [], "ECLIQ": []} %}
{%  set capacitance_regions = {"PS": [], "circuit": [], "EE": [], "ESC": [], "CLIQ": [], "ECLIQ": []} %}
{%  set resistance_regions = {"PS": [], "circuit": [], "EE": [], "ESC": [], "CLIQ": [], "ECLIQ": []} %}
{%  set diode_regions = {"PS": [], "EE": [], "ESC": []} %}
{%  set voltagesource_regions = {"CLIQ": []} %}
{%  set currentsource_regions = {"PS": [], "ECLIQ": []} %}
{%  set thyristor_regions = {"ESC": [], "CLIQ": []} %}
{%  set varistor_regions = {"EE": []} %}
{%  set switch_regions = {"EE":[],"CLIQ":[],"ESC":[]}  -%}

{#- Power Supply Regions #}
{%  do inductance_regions["PS"].extend(["L_1", "L_2", "L_3", "L_crowbar", "L_c_r"]) %}
{%  do capacitance_regions["PS"].append("C") %}
{%  do resistance_regions["PS"].extend(["R_1", "R_2", "R_3", "R_crowbar", "R_c_r"]) %}
{%  do diode_regions["PS"].extend(["Ud_crowbar", "Ud_c_r"]) %}
{%  do currentsource_regions["PS"].append("currentsource") -%}

{#-  circuit#}
{%- if dm.circuit.R_circuit  %}
{%    do resistance_regions["circuit"].append("R_circuit") -%}
{%  endif -%}

{#- Energy Extraction Regions #}
{%- if flag_active["EE"] == 1 %}
{%    do inductance_regions["EE"].extend(["L", "L_c", "L_s","L_n", "L_c_n", "L_s_n"]) %}
{%    do capacitance_regions["EE"].extend(["C","C_n"]) %}
{%    do resistance_regions["EE"].extend(["R_c", "R_s","R_c_n", "R_s_n"]) %}
{%    do diode_regions["EE"].extend(["Ud_snubber", "Ud_switch","Ud_snubber_n", "Ud_switch_n"]) %}
{%    do varistor_regions["EE"].extend(["V_EE","V_EE_n"]) %}
{%    do switch_regions["EE"].extend(["R_switch","R_switch_n"])%}
{% endif -%}

{#- CLIQ Regions #}
{%- if flag_active["CLIQ"] == 1 %}
{%    for i in range(1, CLIQ_dict["Units"] + 1) %}
{%      do resistance_regions["CLIQ"].extend(["R_" ~ i]) %}
{%      do inductance_regions["CLIQ"].append("L_" ~ i) %}
{%      do capacitance_regions["CLIQ"].append("C_" ~ i) %}
{%      do switch_regions["CLIQ"].append("R_switch_" ~ i)%}
{%    endfor %}
{%  endif -%}

{#- ESC Regions #}
{%  if flag_active["ESC"] == 1 %}
{%    for i in range(1, ESC_dict["Units"] + 1) %}
{%      do capacitance_regions["ESC"].extend(["C1_" ~ i, "C2_" ~ i]) %}
{%      do resistance_regions["ESC"].extend([ "R_leads_" ~ i, "R_unit_" ~ i]) %}
{%      do inductance_regions["ESC"].extend(["L_" ~ i,"L_Diode_" ~ i]) %}
{%      do diode_regions["ESC"].append("Ud_Diode_" ~ i) %}
{%      do switch_regions["ESC"].append("R_switch_" ~ i)%}
{%    endfor %}
{%  endif %}

{#- ECLIQ Regions #}
{%  if flag_active["ECLIQ"] == 1 %}
{%    for i in range(1, ECLIQ_dict["Units"] + 1) %}
{%      do currentsource_regions["ECLIQ"].append("currentsource_" ~ i) %}
{%      do inductance_regions["ECLIQ"].append("L_leads_" ~ i) %}
{%      do resistance_regions["ECLIQ"].append("R_leads_" ~ i) %}
{%    endfor %}
{%  endif -%}

{%-  set counter = {"counter_regions": 0} -%}


{#- Power Supply  #}
{%-  for ind,elem in enumerate(currentsource_regions["PS"])  -%} 
{%    do regions_CC.update({"Omega_PS_" ~ elem:magnet_reg_lim +counter["counter_regions"] + 1}) -%} << increment(counter, "counter_regions") >>
{%- endfor -%}
{%  for ind,elem in enumerate(resistance_regions["PS"])  -%} 
{%    do regions_CC.update({"Omega_PS_" ~ elem:magnet_reg_lim +counter["counter_regions"] + 1}) -%} << increment(counter, "counter_regions") >>
{%- endfor -%}
{%  for ind,elem in enumerate(inductance_regions["PS"])  -%} 
{%    do regions_CC.update({"Omega_PS_" ~ elem:magnet_reg_lim +counter["counter_regions"] + 1}) -%} << increment(counter, "counter_regions") >>
{%- endfor -%}
{%  for ind,elem in enumerate(diode_regions["PS"])  -%} 
{%    do regions_CC.update({"Omega_PS_" ~ elem:magnet_reg_lim +counter["counter_regions"] + 1}) -%} << increment(counter, "counter_regions") >>
{%- endfor -%}
{%  for ind,elem in enumerate(capacitance_regions["PS"])  -%} 
{%    do regions_CC.update({"Omega_PS_" ~ elem:magnet_reg_lim +counter["counter_regions"] + 1}) -%} << increment(counter, "counter_regions") >>
{%- endfor -%}

{%- do flag_active.update({"CS": 1}) %}
{%  do flag_active.update({"R": 1}) %}
{%  do flag_active.update({"L": 1}) %}
{%  do flag_active.update({"C": 1}) %}
{%  do flag_active.update({"D": 1}) %}

{#- Energy Extraction #}
{%  if flag_active["EE"]==1%}
{%    for ind,elem in enumerate(varistor_regions["EE"])  -%} 
{%      do regions_CC.update({"Omega_EE_" ~ elem:magnet_reg_lim +counter["counter_regions"] + 1}) -%} << increment(counter, "counter_regions") >>
{%-   endfor -%}
{%    for ind,elem in enumerate(resistance_regions["EE"])  -%} 
{%      do regions_CC.update({"Omega_EE_" ~ elem:magnet_reg_lim +counter["counter_regions"] + 1}) -%} << increment(counter, "counter_regions") >>
{%-   endfor -%}
{%    for ind,elem in enumerate(inductance_regions["EE"])  -%} 
{%      do regions_CC.update({"Omega_EE_" ~ elem:magnet_reg_lim +counter["counter_regions"] + 1}) -%} << increment(counter, "counter_regions") >>
{%-   endfor -%}
{%    for ind,elem in enumerate(diode_regions["EE"])  -%} 
{%      do regions_CC.update({"Omega_EE_" ~ elem:magnet_reg_lim +counter["counter_regions"] + 1}) -%} << increment(counter, "counter_regions") >>
{%-   endfor -%}
{%    for ind,elem in enumerate(capacitance_regions["EE"])  -%} 
{%      do regions_CC.update({"Omega_EE_" ~ elem:magnet_reg_lim +counter["counter_regions"] + 1}) -%} << increment(counter, "counter_regions") >>
{%-   endfor -%}
{%    for ind,elem in enumerate(switch_regions["EE"])  -%} 
{%      do regions_CC.update({"Omega_EE_" ~ elem:magnet_reg_lim +counter["counter_regions"] + 1}) -%} << increment(counter, "counter_regions") >>
{%-   endfor -%}
{%    do flag_active.update({"SW": 1}) %}
{%    do flag_active.update({"V": 1}) %}
{%  else%}
{%    do flag_active.update({"V": 0}) %}
{%    do flag_active.update({"SW": 0}) %}
{%  endif%}

{#- Circuit#}
{%  if dm.circuit.R_circuit %}
{%    for ind,elem in enumerate(resistance_regions["circuit"])  -%} 
{%      do regions_CC.update({"Omega_circuit_" ~ elem:magnet_reg_lim +counter["counter_regions"] + 1}) -%}
<< increment(counter, "counter_regions") >>
{%-   endfor -%}
{%  endif  -%}

{#- CLIQ #}
{%  if flag_active["CLIQ"]==1 -%}
{%    for i in range(1, CLIQ_dict["Units"] + 1) %}{# It uses N_ht so that it would potentially allow to have up to N_ht/2 CLIQ units(defined by CLIQ units) #}
{%      for ind,elem in enumerate(resistance_regions["CLIQ"])  -%} 
{%        do regions_CC.update({"Omega_CLIQ_" ~ elem :magnet_reg_lim +counter["counter_regions"] + 1}) -%}  << increment(counter, "counter_regions") >>
{%-      endfor -%}
{%      for ind,elem in enumerate(inductance_regions["CLIQ"])  -%} 
{%        do regions_CC.update({"Omega_CLIQ_" ~ elem :magnet_reg_lim +counter["counter_regions"] + 1}) -%}  << increment(counter, "counter_regions") >>
{%-      endfor -%}
{%      for ind,elem in enumerate(capacitance_regions["CLIQ"])  -%} 
{%        do regions_CC.update({"Omega_CLIQ_" ~ elem :magnet_reg_lim +counter["counter_regions"] + 1}) -%}  << increment(counter, "counter_regions") >>
{%-     endfor -%}
{%      for ind,elem in enumerate(switch_regions["CLIQ"])  -%} 
{%        do regions_CC.update({"Omega_CLIQ_" ~ elem :magnet_reg_lim +counter["counter_regions"] + 1}) -%}  << increment(counter, "counter_regions") >>
{%-     endfor -%}
{%    endfor %}
{%        do flag_active.update({"SW": 1}) %}
{%  endif %}

{#- E-CLIQ #}
{%  if flag_active["ECLIQ"]==1 -%}
{%    for i in range(1, ECLIQ_dict["Units"] + 1) %}{# It uses N_ht so that it would potentially allow to have up to N_ht ECLIQ units(defined by ECLIQ units) #}
{%      for ind,elem in enumerate(currentsource_regions["ECLIQ"])  -%} 
{%        do regions_CC.update({"Omega_ECLIQ_" ~ elem:magnet_reg_lim +counter["counter_regions"] + 1}) -%}  << increment(counter, "counter_regions") >>
{%-      endfor -%}
{%      for ind,elem in enumerate(resistance_regions["ECLIQ"])  -%} 
{%        do regions_CC.update({"Omega_ECLIQ_" ~ elem:magnet_reg_lim +counter["counter_regions"] + 1}) -%}  << increment(counter, "counter_regions") >>
{%-      endfor -%}
{%      for ind,elem in enumerate(inductance_regions["ECLIQ"])  -%} 
{%        do regions_CC.update({"Omega_ECLIQ_" ~ elem:magnet_reg_lim +counter["counter_regions"] + 1}) -%}  << increment(counter, "counter_regions") >>
{%-      endfor -%}
{%    endfor %}
{%  endif %}

{#- ESC #}
{%  if flag_active["ESC"]==1 -%}
{%    for i in range(1, ESC_dict["Units"] + 1) %}{# It uses N_ht so that it would potentially allow to have up to N_ht ESC units(defined by ESC units) #}
{%      for ind,elem in enumerate(capacitance_regions["ESC"])  -%} 
{%        do regions_CC.update({"Omega_ESC_" ~ elem:magnet_reg_lim +counter["counter_regions"] + 1}) -%}  << increment(counter, "counter_regions") >>
{%-      endfor -%}
{%      for ind,elem in enumerate(resistance_regions["ESC"])  -%} 
{%        do regions_CC.update({"Omega_ESC_" ~ elem:magnet_reg_lim +counter["counter_regions"] + 1}) -%}  << increment(counter, "counter_regions") >>
{%-      endfor -%}
{%      for ind,elem in enumerate(inductance_regions["ESC"])  -%} 
{%        do regions_CC.update({"Omega_ESC_" ~ elem:magnet_reg_lim +counter["counter_regions"] + 1}) -%}  << increment(counter, "counter_regions") >>
{%-      endfor -%}
{%      for ind,elem in enumerate(diode_regions["ESC"])  -%} 
{%        do regions_CC.update({"Omega_ESC_" ~ elem:magnet_reg_lim +counter["counter_regions"] + 1}) -%}  << increment(counter, "counter_regions") >>
{%-      endfor -%}
{%      for ind,elem in enumerate(switch_regions["ESC"])  -%} 
{%        do regions_CC.update({"Omega_ESC_" ~ elem:magnet_reg_lim +counter["counter_regions"] + 1}) -%}  << increment(counter, "counter_regions") >>
{%-      endfor -%}
{%    endfor -%}
{%        do flag_active.update({"SW": 1}) %}
{% endif -%}

{%- for region, number in regions_CC.items() %}
  << region >> = Region[<< number >>];
{%  endfor -%}
{%  set name_components = ["resistance","inductance","capacitance","diode","varistor","currentsource","switch"]%}
{%  do CC_dict.extend([name_components,resistance_regions,inductance_regions,capacitance_regions, diode_regions, varistor_regions, currentsource_regions,switch_regions])%}
{%- endmacro -%}

{% macro groups_FCC(dm,rm_EM, flag_active,CLIQ_dict,ECLIQ_dict,ESC_dict,CC_dict,aux) %}

{%-  set regions = []  %}

{%-  for i in range(len(CC_dict)-1)%}
{%    for j in CC_dict[i+1].items()%}
{%      for k in j[1]%}
{%        do regions.append("Omega_" ~ j[0] ~ "_" ~ k)%}
{%      endfor  %}
{%    endfor%}
  Omega_<<CC_dict[0][i]>> = Region[{<< regions|join(', ')>>}];
{%  do regions.clear() %}
{%  endfor%}

  // Omega_resistance += Region[{Omega_switch}];

  Omega_circuit = Region[{ Omega_currentsource{% if flag_active["R"] == 1 -%},  Omega_resistance{% endif %}
{%    if flag_active["D"] == 1 -%},  Omega_diode{% endif %}
{%    if flag_active["C"] == 1 -%},  Omega_capacitance{% endif %}
{%    if flag_active["L"] == 1 -%},  Omega_inductance{% endif %}
{%    if flag_active["Th"] == 1 -%}, Omega_thyristor{% endif %}
{%    if flag_active["V"] == 1 -%},  Omega_varistor{% endif %}
{%    if flag_active["VS"] == 1 -%}, Omega_voltagesource{% endif %}, Omega_switch }];

  //----------------------------
  {%  for i in range(len(CC_dict)-1)%}
  {%    for j in CC_dict[i+1].items()%}
  {%      for k in j[1] if j[0] == "PS"%}
  {%        do regions.append("Omega_" ~ j[0] ~ "_" ~ k)%}
  {%      endfor  %}
  {%    endfor%}
  {%  endfor%}
  Omega_PS = Region[{<<regions|join(', ')>>}];
  {%  do regions.clear() %}

{%-    if flag_active["EE"] == 1%}
{%  for i in range(len(CC_dict)-1)%}
{%    for j in CC_dict[i+1].items()%}
{%      for k in j[1] if j[0] == "EE"%}
{%        do regions.append("Omega_" ~ j[0] ~ "_" ~ k)%}
{%      endfor  %}
{%    endfor%}
{%  endfor%}
  Omega_EE = Region[{<<regions|join(', ')>>}];
{%  do regions.clear() %}
{%    endif%}

{%-    if flag_active["CLIQ"] == 1%}
{%  for i in range(len(CC_dict)-1)%}
{%    for j in CC_dict[i+1].items()%}
{%      for k in j[1] if j[0] == "CLIQ"%}
{%        do regions.append("Omega_" ~ j[0] ~ "_" ~ k)%}
{%      endfor  %}
{%    endfor%}
{%  endfor%}
  Omega_CLIQ = Region[{<<regions|join(', ')>>}];
{%  do regions.clear() %}
{%    endif%}

{%-    if flag_active["ECLIQ"] == 1%}
{%  for i in range(len(CC_dict)-1)%}
{%    for j in CC_dict[i+1].items()%}
{%      for k in j[1] if j[0] == "ECLIQ"%}
{%        do regions.append("Omega_" ~ j[0] ~ "_" ~ k)%}
{%      endfor  %}
{%    endfor%}
{%  endfor%}
  Omega_ECLIQ = Region[{<<regions|join(', ')>>}];
{%  do regions.clear() %}
    // ECLIQ coils
{% set ecliq_ht_names_EM = [] %}
{% set ecliq_ht_names_TH = [] %}
{% for ht in aux.half_turns.ADD_COILS %}
    {% do ecliq_ht_names_EM.append('ht' ~ ht ~ '_EM') %}
    {% do ecliq_ht_names_TH.append('ht' ~ ht ~ '_TH') %}
{% endfor %}
Omega_ECLIQ_ht_EM = Region[{<< ecliq_ht_names_EM | join(', ') >>}];
Omega_ECLIQ_ht_TH = Region[{<< ecliq_ht_names_TH | join(', ') >>}];
{%    endif%}

{%-    if flag_active["ESC"] == 1%}
{%  for i in range(len(CC_dict)-1)%}
{%    for j in CC_dict[i+1].items()%}
{%      for k in j[1] if j[0] == "ESC"%}
{%        do regions.append("Omega_" ~ j[0] ~ "_" ~ k)%}
{%        do ESC_dict.Comp.append("Omega_" ~ j[0] ~ "_" ~ k) %}
{%      endfor  %}
{%    endfor%}
{%  endfor%}
  Omega_ESC = Region[{<<regions|join(', ')>>}];
{%  do regions.clear() %}

{% set esc_ht_names = [] %}
{% for ht in aux.half_turns.ADD_COILS %}
    {% do esc_ht_names.append('ht' ~ ht ~ '_EM') %}
{% endfor %}
Omega_ESC_ht = Region[{<< esc_ht_names | join(', ') >>}];
{%    endif%}


{% endmacro %}

{%- macro function_FCC(nc,dm,rm_EM, flag_active,CLIQ_dict,ECLIQ_dict,ESC_dict,CC_dict,aux) -%}
  // Current source
  source_current_fct[] = 
  $Time <= <<dm.power_supply.t_control_LUT[ 0 ]>> ? <<dm.power_supply.I_control_LUT[ 0 ]>> :
  {% for i in range(len(dm.power_supply.t_control_LUT) - 1) %}
    $Time <= <<dm.power_supply.t_control_LUT[i + 1]>> ?
    <<dm.power_supply.I_control_LUT[i]>> + 
    (<<dm.power_supply.I_control_LUT[i + 1]>> - <<dm.power_supply.I_control_LUT[i]>>) / 
    (<<dm.power_supply.t_control_LUT[i + 1]>> - <<dm.power_supply.t_control_LUT[i]>>) * 
    ($Time - <<dm.power_supply.t_control_LUT[i]>>) :
{% endfor %}
  <<dm.power_supply.I_control_LUT[-1]>>; // Default fallback

{%  if flag_active["ECLIQ"] %}
//ECLIQ - CSV Piecewise currentsources
{%    if dm.quench_protection.e_cliq.source_type == 'piecewise' and dm.quench_protection.e_cliq.piecewise.csv_file is not none %}
{%        if dm.quench_protection.e_cliq.piecewise.time_multiplier %}t_coeff = <<dm.quench_protection.e_cliq.piecewise.time_multiplier>>; {%else%} t_coeff = 1;{%endif%}
{%        if dm.quench_protection.e_cliq.piecewise.current_multiplier %}I_coeff = <<dm.quench_protection.e_cliq.piecewise.current_multiplier>>; {%else%} I_coeff = 1;{%endif%}

{%          for i in range(1,ECLIQ_dict["Units"]+1)%}
  <<'Omega_ECLIQ_currentsource_'~i>>_fct[] = 
    $Time < t_coeff * <<aux.e_cliq['source_current_'~i]['t_control_LUT'][ 0 ]>> ? I_coeff * <<aux.e_cliq['source_current_'~i]['I_control_LUT'][ 0 ]>>:
{%            for j in range(len(aux.e_cliq['source_current_'~i]['t_control_LUT']) - 1) %}
    $Time < t_coeff * <<aux.e_cliq['source_current_'~i]['t_control_LUT'][ j+1 ]>> ?
    I_coeff * <<aux.e_cliq['source_current_'~i]['I_control_LUT'][ j ]>>+ 
    I_coeff * (<<aux.e_cliq['source_current_'~i]['I_control_LUT'][ j+1 ]>> - <<aux.e_cliq['source_current_'~i]['I_control_LUT'][ j ]>>) / 
    (<<aux.e_cliq['source_current_'~i]['t_control_LUT'][ j+1 ]>> - <<aux.e_cliq['source_current_'~i]['t_control_LUT'][ j ]>>) * 
    ($Time - <<aux.e_cliq['source_current_'~i]['t_control_LUT'][ j ]>>) :
{%            endfor %}
    I_coeff * <<aux.e_cliq['source_current_'~i]['I_control_LUT'][ -1 ]>>; // Default fallback
{%        endfor  %}
{%    else%}
{%      if dm.quench_protection.e_cliq.source_type == 'piecewise'%}
{%        if dm.quench_protection.e_cliq.piecewise.time_multiplier %}t_coeff = <<dm.quench_protection.e_cliq.piecewise.time_multiplier>>; {%else%} t_coeff = 1;{%endif%}
{%        if dm.quench_protection.e_cliq.piecewise.current_multiplier %}I_coeff = <<dm.quench_protection.e_cliq.piecewise.current_multiplier>>; {%else%} I_coeff = 1;{%endif%}

{%          for i in range(1,ECLIQ_dict["Units"]+1)%}
  <<'Omega_ECLIQ_currentsource_'~i>>_fct[] = 
    $Time < t_coeff * <<dm.quench_protection.e_cliq.piecewise.times[ 0 ]>> ? I_coeff * <<dm.quench_protection.e_cliq.piecewise.currents[ 0 ]>>:
{%            for i in range(len(dm.quench_protection.e_cliq.piecewise.times) - 1) %}
    $Time < t_coeff * <<dm.quench_protection.e_cliq.piecewise.times[ i + 1 ]>> ?
    I_coeff * <<dm.quench_protection.e_cliq.piecewise.currents[ i ]>> + 
    I_coeff * (<<dm.quench_protection.e_cliq.piecewise.currents[ i + 1 ]>> - <<dm.quench_protection.e_cliq.piecewise.currents[ i ]>>) / 
    (<<dm.quench_protection.e_cliq.piecewise.times[ i + 1 ]>> - <<dm.quench_protection.e_cliq.piecewise.times[ i ]>>) * 
    ($Time - <<dm.quench_protection.e_cliq.piecewise.times[ i ]>>) :
{%            endfor %}
    I_coeff * <<dm.quench_protection.e_cliq.piecewise.currents[-1]>>; // Default fallback
{%        endfor  %}
{%    elif dm.quench_protection.e_cliq.source_type == 'sine'%}
{%        for i in range(1,ECLIQ_dict["Units"]+1)%}
    <<'Omega_ECLIQ_currentsource_'~i>>_fct[]=$Time<=<<dm.quench_protection.e_cliq.t_trigger[i-1]>>?0:$Time<= <<dm.quench_protection.e_cliq.sine.number_of_periods>> /<<dm.quench_protection.e_cliq.sine.frequency>> ? <<dm.quench_protection.e_cliq.sine.current_amplitude>>*<<dm.quench_protection.e_cliq.sine.number_of_turns>> * Sin[2*Pi*<<dm.quench_protection.e_cliq.sine.frequency>> * $Time] : 0.0;

{%        endfor%}

{%      endif %}
{%    endif%}
{%  endif%}

  // Diode Shockley model w/ V(I) U0 can only be 0.7 volts
{%  if flag_active['D']== 1 %}
    VTh = 25.86e-3;
    Is = 10e-12;
    eps = 1e-9;
    V_ref = 0.7;
    n[Omega_PS_Ud_crowbar] = <<dm.power_supply.Ud_crowbar>>/V_ref;
    n[Omega_PS_Ud_c_r] = <<dm.power_supply.Ud_c_r>>/V_ref;
{%    if flag_active["EE"] == 1%}
    n[Omega_EE_Ud_snubber] = <<dm.quench_protection.energy_extraction.Ud_snubber>>/V_ref;
    n[Omega_EE_Ud_switch] = <<dm.quench_protection.energy_extraction.Ud_switch>>/V_ref;
    n[Omega_EE_Ud_snubber_n] = <<dm.quench_protection.energy_extraction.Ud_snubber_n>>/V_ref;
    n[Omega_EE_Ud_switch_n] = <<dm.quench_protection.energy_extraction.Ud_switch_n>>/V_ref;
{%    endif%}
{%    if flag_active["ESC"] == 1%}
{%      for i in range(1,ESC_dict["Units"]+1)%}
    n[<<'Omega_ESC_Ud_Diode_'~i>>] = <<dm.quench_protection.esc.Ud_Diode[i-1]>>/V_ref;
{%      endfor %}
{%    endif%}
    R[Omega_diode] = $1 < eps ? 1e6 : VTh * n[] * Log[1 + $1 / Is] > n[]*V_ref ? n[]*V_ref/$1 : VTh * n[] * Log[1 + $1 / Is]/ $1;
    //dRdI[Omega_diode] = $1 < eps ? -1e6 : n[] * Vth * ($1 / (Is + $1)-Log[1 + $1 /Is]) / $1 ^2
{%  endif %}

  // Thyristor model
{%  if flag_active['Th']== 1 %}
  R_th_off=1e12;
  eps = 1e-9;
{%    if flag_active["CLIQ"]==1 -%}
  th_switch_time = << dm.quench_protection.cliq.t_trigger >>;
  R[Omega_thyristor] = $Time < th_switch_time ? R_th_off : $1 < eps ? 1e6 : V_ref * Log[1 + $1 / Is] / $1;
  //dRdI[Omega_thyristor] = $1 < eps ? -V_ref * (2 - Is) / 2 / Is^2 : -V_ref * (($1 + Is) * Log[1 + $1 / Is] - $1) / ($1)^2 / ($1 + Is);
{%    else %}
{%      for i in range(1,ESC_dict["Units"]+1) %}
  th_switch_time = << dm.quench_protection.esc.t_trigger[i-1] >>;
  R[Omega_ESC_thyristor1_<<i>>] = $Time < th_switch_time ? R_th_off : $1 < eps ? 1e6 : V_ref * Log[1 + $1 / Is] / $1;
  R[Omega_ESC_thyristor2_<<i>>] = $Time < th_switch_time ? R_th_off : $1 < eps ? 1e6 : V_ref * Log[1 + $1 / Is] / $1;
{%      endfor %}
{%    endif %}
{%  endif %}

  // Varistor model
{%  if flag_active['V']== 1 %}
    power_R_EE[Omega_EE_V_EE] = <<dm.quench_protection.energy_extraction.power_R_EE>>;
    power_R_EE[Omega_EE_V_EE_n] = <<dm.quench_protection.energy_extraction.power_R_EE_n>>;
    R_EE[Omega_EE_V_EE] = <<dm.quench_protection.energy_extraction.R_EE>>;
    R_EE[Omega_EE_V_EE_n] = <<dm.quench_protection.energy_extraction.R_EE_n>>;
    EE_resistance_inactive = 1e-6;
    R[Omega_EE_V_EE] = $Time < <<dm.quench_protection.energy_extraction.t_trigger>>? EE_resistance_inactive : R_EE[] * ($1)^power_R_EE[]; // Varistor model
    R[Omega_EE_V_EE_n] = $Time < <<dm.quench_protection.energy_extraction.t_trigger_n>>? EE_resistance_inactive : R_EE[] * ($1)^power_R_EE[]; // Varistor model
{%  endif %}

  // Fixed inductances
{%  if flag_active['L'] == 1 %}
{%    for i in CC_dict[2]["PS"] %}
    L[<<"Omega_PS_" ~ i>>] = <<dm.power_supply[i]>>;
{%    endfor  %}
{%    if flag_active["CLIQ"]==1 %}
{%      for i in CC_dict[2]["CLIQ"] %}
    L[<<"Omega_CLIQ_" ~ i>>] ={%if  dm.quench_protection.cliq.L  %} << dm.quench_protection.cliq.L >>{% else %}0.0 {% endif %};
{%      endfor  %}
{%    endif%} 
{%    if flag_active["EE"]==1 %}
{%      for i in CC_dict[2]["EE"] %}
    L[<<"Omega_EE_" ~ i>>] ={%if  dm.quench_protection.energy_extraction[i] %} << dm.quench_protection.energy_extraction[i] >>{% else %}0.0 {% endif %};
{%      endfor  %} 
{%    endif %}
{%    if flag_active["ECLIQ"]==1 %}
{%      for ind,elem in enumerate(CC_dict[2]["ECLIQ"]) %}
    L[<<"Omega_ECLIQ_" ~ elem>>] ={%if  dm.quench_protection.e_cliq.L_leads[ind]  %} << dm.quench_protection.e_cliq.L_leads[ind] >>{% else %}0.0 {% endif %};
{%      endfor  %} 
{%    endif %}
{%    if flag_active["ESC"]==1 %}
{%      set counter ={"counter_esc":1}%}
{%      for i in range(1,ESC_dict["Units"]+1)%}
    L[<<'Omega_ESC_L_'~i>>] = <<dm.quench_protection.esc.L[i-1]>>;
    L[<<'Omega_ESC_L_Diode_'~i>>] = <<dm.quench_protection.esc.L_Diode[i-1]>>;
{%      endfor %}
{%    endif %}
{%  endif %}

  // Fixed capacitances
{%  if flag_active['C'] == 1 %}
{%    for i in CC_dict[3]["PS"] %}
    C[<<"Omega_PS_" ~ i>>] = <<dm.power_supply[i]>>;
{%    endfor  %}
{%    if flag_active["CLIQ"]==1 %}
{%      for i in CC_dict[3]["CLIQ"] %}
    C[<<"Omega_CLIQ_" ~ i>>] ={%if  dm.quench_protection.cliq.C  %} << dm.quench_protection.cliq.C >>{% else %}0.0 {% endif %};
{%      endfor  %}
{%    endif%} 
{%    if flag_active["EE"]==1 %}
{%      for i in CC_dict[3]["EE"] %}
    C[<<"Omega_EE_" ~ i>>] ={%if  dm.quench_protection.energy_extraction[i]  %} << dm.quench_protection.energy_extraction[i] >>{% else %}0.0 {% endif %};
{%      endfor  %} 
{%    endif %}
{%    if flag_active["ESC"]==1 %}
{%      for i in range(1,ESC_dict["Units"]+1)%}
    C[<<'Omega_ESC_C1_'~i>>] = 2 * <<dm.quench_protection.esc.C[i-1]>>;
    C[<<'Omega_ESC_C2_'~i>>] = 2 * <<dm.quench_protection.esc.C[i-1]>>;
{%      endfor %}
{%    endif %}
{%  endif %}

  // Fixed resistances / switches
  R_switch_off = 1e6;
  R_switch_on = 1e-10;
{%  if flag_active['R'] == 1 %}
{%    for i in CC_dict[1]["PS"] %}
    R[<<"Omega_PS_" ~ i>>] = <<dm.power_supply[i]>>;
{%    endfor  %}
{%    for i in CC_dict[1]["circuit"] %}
    R[<<"Omega_circuit_" ~ i>>] = <<dm.circuit[i]>>;
{%    endfor  %}
{%    if flag_active["CLIQ"]==1 %}
{%      for i in CC_dict[1]["CLIQ"] %}
    R[<<"Omega_CLIQ_" ~ i>>] ={%if  dm.quench_protection.cliq.R  %} << dm.quench_protection.cliq.R >>{% else %}0.0 {% endif %};
{%      endfor  %}
{%      for i in CC_dict[7]["CLIQ"] %}
    R[<<"Omega_CLIQ_" ~ i>>] =$Time<= <<dm.quench_protection.cliq.t_trigger>> ? R_switch_off : R_switch_on;
    Coef_switch[<<"Omega_CLIQ_" ~ i>>]=$Time < <<dm.quench_protection.cliq.t_trigger>> ? 0:1 ;
{%      endfor  %}
{%    endif%} 
{%    if flag_active["EE"]==1 %}
{%      for i in CC_dict[1]["EE"] %}
    R[<<"Omega_EE_" ~ i>>] ={%if  dm.quench_protection.energy_extraction[i]  %} << dm.quench_protection.energy_extraction[i] >>{% else %}0.0 {% endif %};
{%      endfor  %}
    R[Omega_EE_R_switch] = $Time<= <<dm.quench_protection.energy_extraction.t_trigger>> ? R_switch_on : R_switch_off;
    R[Omega_EE_R_switch_n] = $Time<= <<dm.quench_protection.energy_extraction.t_trigger_n>> ? R_switch_on : R_switch_off;
    Coef_switch[Omega_EE_R_switch_n]=$Time < <<dm.quench_protection.energy_extraction.t_trigger_n>> ? 1:0 ;
    Coef_switch[Omega_EE_R_switch]=$Time < <<dm.quench_protection.energy_extraction.t_trigger>> ? 1:0 ;
{%    endif %}
{%    if flag_active["ECLIQ"]==1 %}
{%      for ind,elem in enumerate(CC_dict[1]["ECLIQ"]) %}
    R[<<"Omega_ECLIQ_" ~ elem>>] ={%if  dm.quench_protection.e_cliq.R_leads[ind]  %} << dm.quench_protection.e_cliq.R_leads[ind] >>{% else %}0.0 {% endif %};
{%      endfor  %} 
{%    endif %}
{%    if flag_active["ESC"]==1 %}
{%      for i in range(1,ESC_dict["Units"]+1)%}
    R[<<'Omega_ESC_R_leads_'~i>>] =  <<dm.quench_protection.esc.R_leads[i-1]>>;
    R[<<'Omega_ESC_R_unit_'~i>>] = <<dm.quench_protection.esc.R_unit[i-1]>>;
    R[<<"Omega_ESC_R_switch_" ~ i>>] =$Time<= <<dm.quench_protection.esc.t_trigger[i-1]>> ? R_switch_off : R_switch_on;
    Coef_switch[<<"Omega_ESC_R_switch_" ~ i>>]=$Time < <<dm.quench_protection.esc.t_trigger[i-1]>> ? 0:1 ;
{%      endfor %}
{%    endif %}
{%  endif %}
{% endmacro %}

{%- macro constraints_FCC(dm,rm_EM, flag_active, init_ht, end_ht,CLIQ_dict,ECLIQ_dict, ESC_dict,CC_dict,aux,pol_) %}
{%  set magnet_reg_lim = aux.half_turns.max_reg %} {# Define the end of the magnet regions numbering #}
{%  set N_ht = end_ht -%}
  // Power Supply
  // Circuit coupling constraints
  { Name ElectricalCircuit; Type Network;
    Case Circuit1 { // Describes node connection of branches
{%    set count={"count_br":2}%}
    //Main Loop
      // Power supply
      { Region Omega_PS_currentsource; Branch {1, 2}; }
      { Region Omega_PS_R_1; Branch {2,3}; }
      { Region Omega_PS_L_1; Branch {3,4}; }
      { Region Omega_PS_R_2; Branch {4,5}; }
      { Region Omega_PS_L_2; Branch {5,6}; }
{%        set br_circ_end = 6%}

      // EE & Circuit
{%    if flag_active["EE"] == 1%}
      { Region Omega_EE_L; Branch {6,7}; }
      { Region Omega_EE_V_EE; Branch {7,8}; }

{%      set br_circ_end = 8%}
{%      if dm.circuit.R_circuit %}
      { Region Omega_circuit_R_circuit; Branch {8,9}; }
{%        set br_circ_end = 9%}
{%      endif%}
{%    else%}
{%      if dm.circuit.R_circuit %}
      { Region Omega_circuit_R_circuit; Branch {6,7}; }
{%        set br_circ_end = 7%}
{%      endif%}
{%    endif%}

      // Magnet
{%    set br_mag_end = N_ht + br_circ_end %}
{% if pol_["first"] == 1%}
{% set count_polarity = 0 %}
{% else %}
{% set count_polarity = 1 %}
{% endif %}
{%    for elec, lead in zip(dm.magnet.solve.coil_windings.electrical_pairs.overwrite_electrical_order[init_ht:end_ht], range(len(dm.magnet.solve.coil_windings.electrical_pairs.overwrite_electrical_order[init_ht:end_ht]))) %}
{%      if loop.last %}
{% if count_polarity == 0 %}
{%        if flag_active["EE"] == 1 or flag_active["CLIQ"] == 1 %}
      { Region ht<< elec >>_EM; Branch { << lead + br_circ_end+1 >>, << lead + br_circ_end >> }; }
{%        else %}
      { Region ht<< elec >>_EM; Branch { 1, << lead + br_circ_end >> }; }
{%        endif %}
{% else %}
{%        if flag_active["EE"] == 1 or flag_active["CLIQ"] == 1 %}
      { Region ht<< elec >>_EM; Branch {  << lead + br_circ_end >>,<< lead + br_circ_end+1 >> }; }
{%        else %}
      { Region ht<< elec >>_EM; Branch {  << lead + br_circ_end >>, 1 }; }
{%        endif %}
{% endif %}
{%      else %}
{%        if (loop.index+count_polarity) is even %}
      { Region ht<< elec >>_EM; Branch { << lead + br_circ_end+1 >>, << lead + br_circ_end >> }; }
{%        else %}
      { Region ht<< elec >>_EM; Branch { << lead + br_circ_end >>, << lead + br_circ_end+1 >> }; }
{%        endif %}
{%      endif %}
{%    endfor %}
{%    set br_ML_end = br_mag_end%}
      // FQPCs

      //EE_n
{%    if flag_active["EE"] == 1%}
      { Region Omega_EE_V_EE_n; Branch {<<br_mag_end>>,<<br_mag_end+1>>}; }
      { Region Omega_EE_L_n; Branch {<<br_mag_end+1>>,1}; }
{%    set br_ML_end = br_mag_end+1%}
{%    endif%}

    //Parallel loops
    { Region Omega_PS_C; Branch {4,<<br_ML_end+1>>}; }
    { Region Omega_PS_R_3; Branch {<<br_ML_end+1>>,<<br_ML_end+2>>}; }
    { Region Omega_PS_L_3; Branch {<<br_ML_end+2>>,1}; }
    { Region Omega_PS_R_crowbar; Branch {<<br_ML_end+3>>,2}; }
    { Region Omega_PS_Ud_crowbar; Branch {<<br_ML_end+4>>,<<br_ML_end+3>>}; }
    { Region Omega_PS_L_crowbar; Branch {1,<<br_ML_end+4>>}; }
    { Region Omega_PS_R_c_r; Branch {6,<<br_ML_end+5>>}; }
    { Region Omega_PS_Ud_c_r; Branch {<<br_ML_end+5>>,<<br_ML_end+6>>}; }
    { Region Omega_PS_L_c_r; Branch {<<br_ML_end+6>>,1}; }
{%    set br_PL_end = br_ML_end+6%}
      //EE

{%    if flag_active["EE"] == 1%}
      { Region Omega_EE_Ud_snubber; Branch {8,<<br_PL_end+1>>}; }
      { Region Omega_EE_C; Branch {<<br_PL_end+1>>,<<br_PL_end+2>>}; }
      { Region Omega_EE_R_c; Branch {<<br_PL_end+2>>,<<br_PL_end+3>>}; }
      { Region Omega_EE_L_c; Branch {<<br_PL_end+3>>,6}; }
      { Region Omega_EE_R_switch; Branch {6,<<br_PL_end+4>>}; }
      { Region Omega_EE_L_s; Branch {<<br_PL_end+4>>,<<br_PL_end+5>>}; }
      { Region Omega_EE_R_s; Branch {<<br_PL_end+5>>,<<br_PL_end+6>>}; }
      { Region Omega_EE_Ud_switch; Branch {<<br_PL_end+6>>,8}; }

      { Region Omega_EE_L_c_n; Branch {1,<<br_PL_end+7>>}; }
      { Region Omega_EE_R_c_n; Branch {<<br_PL_end+7>>,<<br_PL_end+8>>}; }
      { Region Omega_EE_C_n; Branch {<<br_PL_end+8>>,<<br_PL_end+9>>}; }
      { Region Omega_EE_Ud_snubber_n; Branch {<<br_PL_end+9>>,<<br_mag_end>>}; }
      { Region Omega_EE_Ud_switch_n; Branch {<<br_mag_end>>,<<br_PL_end+10>>}; }
      { Region Omega_EE_R_s_n; Branch {<<br_PL_end+10>>,<<br_PL_end+11>>}; }
      { Region Omega_EE_L_s_n; Branch {<<br_PL_end+11>>,<<br_PL_end+12>>}; }
      { Region Omega_EE_R_switch_n; Branch {<<br_PL_end+12>>,1}; }
{%      set br_PL_end = br_PL_end+12%}
{%    endif%}

      // CLIQ
{%    if flag_active["CLIQ"] %}
{%      for i in range( CLIQ_dict["Units"]) %}
{%        set cliq_count=4*(i) %}
      { Region Omega_CLIQ_R_<< i+1 >>; Branch {  << br_circ_end + CLIQ_dict["leads"][2*i+1] + 1>>, << br_PL_end + cliq_count +1>> }; }
      { Region Omega_CLIQ_L_<< i+1 >>; Branch { << br_PL_end + cliq_count +1>>, << br_PL_end + cliq_count +2 >> }; }
      { Region Omega_CLIQ_C_<< i+1 >>; Branch { << br_PL_end + cliq_count +2>>, << br_PL_end + cliq_count +3>> }; }
      { Region Omega_CLIQ_R_switch_<< i+1 >>; Branch { <<br_PL_end + cliq_count +3 >>, <<br_circ_end+CLIQ_dict["leads"][2*i]>> }; }
{%      if loop.last %}
{%      endif%}
{%      endfor %}
{%      set br_PL_end = br_PL_end + 4*CLIQ_dict["Units"] %}
{%    endif %}
      // ESC
{%  if flag_active["ESC"]==1 %}
{%    for i in range( ESC_dict["Units"] ) %}
{%      set esc_count=(6+len(aux.half_turns.ADD_COILS[ESC_dict.leads[2*i]:ESC_dict.leads[2*i+1]+1]))*(i) %}
      { Region Omega_ESC_C1_<< i+1 >>; Branch { 1 ,  << br_PL_end  + esc_count +1  >> }; }
      { Region Omega_ESC_R_switch_<< i+1 >>; Branch { << br_PL_end + esc_count + 1  >> ,  << br_PL_end  + esc_count + 2  >> }; }
      {% for lead,elec in enumerate(aux.half_turns.ADD_COILS[ESC_dict.leads[2*i]:ESC_dict.leads[2*i+1]+1]) %}
        {% if loop.index is even %}
      { Region ht<< elec >>_EM; Branch { << lead + br_PL_end  + esc_count + 2 + 1 >>, << lead + br_PL_end  + esc_count + 2 >> }; }
        {% else %}
      { Region ht<< elec >>_EM; Branch { << lead + br_PL_end  + esc_count + 2 >>, << lead + br_PL_end  + esc_count + 2 + 1 >> }; }
        {% endif %}
      {#{ Region Omega_ESC_L_<< i+1 >>; Branch { << br_PL_end  + esc_count + 2  >> ,  << br_PL_end  + esc_count + 3  >> }; }#}
      {% endfor %}
      {% set ESC_coil_l = len(aux.half_turns.ADD_COILS[ESC_dict.leads[2*i]:ESC_dict.leads[2*i+1]+1]) %}
      { Region Omega_ESC_R_leads_<< i +1>>; Branch { << br_PL_end+ESC_coil_l  + esc_count + 2  >>, << br_PL_end+ESC_coil_l  + esc_count + 3  >> }; }
      { Region Omega_ESC_R_unit_<< i +1>>; Branch { << br_PL_end+ESC_coil_l  + esc_count + 3>>, << br_PL_end+ESC_coil_l  + esc_count + 4  >> }; }
      { Region Omega_ESC_L_<< i +1>>; Branch { << br_PL_end+ESC_coil_l  + esc_count + 4>>, << br_PL_end+ESC_coil_l  + esc_count + 5  >> }; }
      { Region Omega_ESC_C2_<< i +1>>; Branch { << br_PL_end+ESC_coil_l + esc_count + 5 >>, 1 }; }
      { Region Omega_ESC_L_Diode_<< i+1 >>; Branch { << br_PL_end  + esc_count + ESC_coil_l + 3>>, << br_PL_end  + esc_count +ESC_coil_l+ 6 >> }; }
      { Region Omega_ESC_Ud_Diode_<< i +1>>; Branch { << br_PL_end  + esc_count+ESC_coil_l + 6>>, << br_PL_end+  + esc_count + 2  >> }; }

{%    endfor %}
{%      set br_PL_end = br_PL_end + 7*ESC_dict["Units"] + len(aux.half_turns.ADD_COILS) %}
{%  endif %}

      // ECLIQ
{%  if flag_active["ECLIQ"]==1 %}
{%    for i in range( ECLIQ_dict["Units"] ) %}
{%      set ecliq_count=(2+len(aux.half_turns.ADD_COILS[ECLIQ_dict.leads[2*i]:ECLIQ_dict.leads[2*i+1]+1]))*(i) %}
      { Region Omega_ECLIQ_currentsource_<< i+1 >>; Branch { 1 ,  << br_PL_end + ecliq_count + 1  >> }; }
      { Region Omega_ECLIQ_L_leads_<< i+1 >>; Branch { << br_PL_end  + ecliq_count + 1  >> ,  << br_PL_end + ecliq_count + 2  >> }; }
      { Region Omega_ECLIQ_R_leads_<< i+1 >>; Branch { << br_PL_end  + ecliq_count + 2  >> ,  << br_PL_end + ecliq_count + 3  >> }; }
      {% for lead,elec in enumerate(aux.half_turns.ADD_COILS[ECLIQ_dict.leads[2*i]:ECLIQ_dict.leads[2*i+1]+1]) %}
        {% if loop.last %}
        { Region ht<< elec >>_EM; Branch { 1, << lead + br_PL_end  + ecliq_count + 3 >> }; }
        {% else %}
          {% if loop.index is even %}
        { Region ht<< elec >>_EM; Branch { << lead + br_PL_end  + ecliq_count + 3 + 1 >>, << lead + br_PL_end  + ecliq_count + 3 >> }; }
          {% else %}
        { Region ht<< elec >>_EM; Branch { << lead + br_PL_end  + ecliq_count + 3 >>, << lead + br_PL_end  + ecliq_count + 3 + 1 >> }; }
          {% endif %}
        {% endif %}
      {% endfor %}
      {% set ECLIQ_coil_l = len(aux.half_turns.ADD_COILS[ECLIQ_dict.leads[2*i]:ECLIQ_dict.leads[2*i+1]+1]) %}
{%    endfor %}
{%  endif %}
    }
  }
  { Name source_current; 
    Case{
      { Region Omega_PS_currentsource; Type Assign; Value 1; TimeFunction source_current_fct[]; }
{%  if flag_active["ECLIQ"]==1 %}
{%    for i in CC_dict[6]["ECLIQ"]%}
        { Region <<'Omega_ECLIQ_' ~ i>>; Type Assign; Value 1; TimeFunction <<'Omega_ECLIQ_' ~ i ~'_fct[]'>>; }
{%    endfor%}
{%  endif %}
    }
  }
  { Name source_voltage; 
    Case{
{%  if flag_active["CLIQ"]==1 %}
{%    for i in CC_dict[3]["CLIQ"]%}
        { Region <<'Omega_CLIQ_' ~ i>>; Type Assign; Value <<dm.quench_protection.cliq.U0>>; }
{%    endfor%}
{%  endif %}
    }
  }
{% endmacro %}

{% macro function_space_FCC(nc,dm,flag_active,SIM_MODE) %}
  { Name CircuitSpace; Type Scalar;
    BasisFunction {
      {
        Name iBF ; NameOfCoef ir ; Function BF_Region ;
          Support Omega_circuit ; Entity Omega_circuit ;
      }
    }

    GlobalQuantity {
      { Name Iz; Type AliasOf       ; NameOfCoef ir; }
      { Name Uz; Type AssociatedWith; NameOfCoef ir; }
  
    }
    Constraint {
      { NameOfCoef Iz; EntityType Region; NameOfConstraint source_current; }
      { NameOfCoef Uz; EntityType Region; NameOfConstraint source_voltage; }
      {% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Mag_dyn' %}
      { NameOfCoef Iz; EntityType Region;
        NameOfConstraint Init_from_Static2; }
        { NameOfCoef Uz; EntityType Region;
          NameOfConstraint Init_from_Static2; }

     {% endif %}
    }
     }

{% endmacro %}

{%- macro formulation_FCC(dm) %}
  { Name is; Type Local; NameOfSpace Hregion_j_Mag_2D; }
  { Name I_mag; Type Global; NameOfSpace Hregion_j_Mag_2D[I_mag]; }
  { Name U_mag; Type Global; NameOfSpace Hregion_j_Mag_2D[U_mag]; }
  { Name Iz; Type Global; NameOfSpace CircuitSpace[Iz]; }
  { Name Uz; Type Global; NameOfSpace CircuitSpace[Uz]; }
{% endmacro %}

{% macro resolution_FCC(dm,rm_EM,flag_active,ESC_dict,ECLIQ_dict) %}
  CreateDirectory["CC_output"];
{% set I_PostPrc_Mult = { 'I_EQ': 'Omega_ECLIQ_currentsource', 'I_ESC': 'Omega_ESC_R_leads', 'I_ESC_Diode': 'Omega_ESC_L_Diode', 'I_ESC_C': 'Omega_ESC_R_unit'} %}
{% set U_PostPrc_ESC = ['ESC_C1','ESC_C2','ESC_R_leads','ESC_R_unit','ESC_L','ESC_L_Diode','ESC_Ud_Diode'] %}
{% set U_PostPrc_ECLIQ = ['ECLIQ_L_leads','ECLIQ_R_leads','ECLIQ_currentsource'] %}


{% set header_I = [] %}
{% for i in dm.magnet.postproc.circuit_coupling.variables_I %}
    {% if i in I_PostPrc_Mult.keys() and (flag_active["ESC"] == 1 or flag_active["ECLIQ"] == 1) %}
        {% for j in range(1, ESC_dict["Units"]+1) %}
            {% do header_I.append(i ~ '_' ~ j) %}
        {% endfor %}
        {% for j in range(1, ECLIQ_dict["Units"]+1) %}
            {% do header_I.append(i ~ '_' ~ j) %}
        {% endfor %}
    {% else %}
        {% do header_I.append(i) %}
    {% endif %}
{% endfor %}

Print["time [s],<< header_I | join(' [A], ') >> [A]", File "CC_output/I.csv"];

{% set header_U = [] %}
{% for i in dm.magnet.postproc.circuit_coupling.variables_U %}
    {% if i in U_PostPrc_ESC and flag_active["ESC"] == 1 %}
        {% for j in range(1, ESC_dict["Units"]+1) %}
            {% do header_U.append(i ~ '_' ~ j) %}
        {% endfor %}
    {% else %}
        {% do header_U.append(i) %}
    {% endif %}
    {% if i in U_PostPrc_ECLIQ and flag_active["ECLIQ"] == 1 %}
        {% for j in range(1, ECLIQ_dict["Units"]+1) %}
            {% do header_U.append(i ~ '_' ~ j) %}
        {% endfor %}
    {% else %}
        {% do header_U.append(i) %}
    {% endif %}
{% endfor %}

Print["time [s],<< header_U | join(' [V], ') >> [V]", File "CC_output/U.csv"];
  Print["time [s],R_mag (Ohm)", File "CC_output/R_mag.csv"];
  Print["time [s],{% if rm_EM.powered['r1_a1'].vol.names %}<<rm_EM.powered['r1_a1'].vol.names|join(' [A], ')>> [A]{% endif %}
                 {% if rm_EM.powered['r1_a2'].vol.names %}, <<rm_EM.powered['r1_a2'].vol.names|join(' [A], ')>> [A]{% endif %}
                 {% if rm_EM.powered['r2_a1'].vol.names %}, <<rm_EM.powered['r2_a1'].vol.names|join(' [A], ')>> [A]{% endif %}
                 {% if rm_EM.powered['r2_a2'].vol.names %}, <<rm_EM.powered['r2_a2'].vol.names|join(' [A], ')>> [A]{% endif %}", File "CC_output/I_mag.csv"];
  Print["time [s],{% if rm_EM.powered['r1_a1'].vol.names %}<<rm_EM.powered['r1_a1'].vol.names|join(' [V], ')>> [V]{% endif %}
                 {% if rm_EM.powered['r1_a2'].vol.names %}, <<rm_EM.powered['r1_a2'].vol.names|join(' [V], ')>> [V]{% endif %}
                 {% if rm_EM.powered['r2_a1'].vol.names %}, <<rm_EM.powered['r2_a1'].vol.names|join(' [V], ')>> [V]{% endif %}
                 {% if rm_EM.powered['r2_a2'].vol.names %}, <<rm_EM.powered['r2_a2'].vol.names|join(' [V], ')>> [V]{% endif %}", File "CC_output/U_mag.csv"];
{% endmacro %}

{%- macro postPr_FCC(nc,dm,flag_active,init_ht,end_ht,aux) %}
  { Name I_;
    Value {
      Term { [ {Iz} ]; In Omega_circuit; }
    }
  }
  { Name U_;
    Value {
      Term { [ {Uz} ]; In Omega_circuit; }
    }
  }
  // Interesting resistances
{%  if flag_active['D'] == 1 %}
  { Name R_diode;
    Value {
      Term { [ R[{Iz}] ]; In Omega_diode; }
    }
  }
{%  endif %}
{%  if flag_active["V"] == 1 %}
  { Name R_v;
    Value {
      Term { [ R[{Iz}] ]; In Omega_varistor; }
    }
  }
{%  endif %}
  { Name js;
    Value {
      Term { [ {is}/area_fct[] ]; In <<nc.omega>><<nc.powered>>_EM; Jacobian Jac_Vol_EM; }
{%  if dm.magnet.solve.electromagnetics.solve_type == "transient" %}
      // Term { [ -sigma[] * (Dt[{a}]) ]; In <<nc.omega>><<nc.induced>>_EM; Jacobian Jac_Vol_EM; }
{%  endif %}
    }
  }
  { Name R_mag;
    Value {
      {%if dm.magnet.solve.thermal.solve_type%}
        Integral{[(Ns/area_fct[])^2 * rho[T_EM_fct[], Norm[{d a}]]*TestQuench[T_EM_fct[],Norm[{d a}],{is}] ]; In <<nc.omega>><<nc.powered>>_EM; Jacobian Jac_Vol_EM; Integration Int_EM; }
    {%else%}
    Integral{[(Ns/area_fct[])^2 * rho[<<dm.magnet.solve.electromagnetics.time_stepping.T_sim>>, Norm[{d a}]]*TestQuench[<<dm.magnet.solve.electromagnetics.time_stepping.T_sim>>,Norm[{d a}],{is}] ]; In <<nc.omega>><<nc.powered>>_EM; Jacobian Jac_Vol_EM; Integration Int_EM; }

    {%endif%}
      }
  }
  {#
  // { Name R_mag;
  //   Value {
  //     {%- for block, ht in aux.half_turns.block.items() %}
  //       {%if dm.magnet.solve.thermal.solve_type%}
  //       Integral{[(Ns[]/area_fct[])^2 * rho[T_EM_fct[], Norm[{d a}]]*TestQuench[T_EM_fct[],Norm[{d a}]*L_ht[],{is}] ]; In <<'Omega_Block_'~block>>; Jacobian Jac_Vol_EM; Integration Int_EM; }
  //       {%else%}
  //   Integral{[(Ns[]/area_fct[])^2 *rho[{d a}] ]; In <<nc.omega>><<nc.powered>>_EM; Jacobian Jac_Vol_EM; Integration Int_EM; }
  //   {%endif%}
  //   {% endfor %}
  //     }
  // }
  #}
  { Name U_mag;
    Value {
      Term { [ {U_mag} ]; In <<nc.omega>><<nc.powered>>_EM; Jacobian Jac_Vol_EM;  }//Jacobian Jac_Vol_EM;
    }
  }
  { Name I_mag;
    Value {
      Term { [ {I_mag} ]; In <<nc.omega>><<nc.powered>>_EM; Jacobian Jac_Vol_EM;  }//Jacobian Jac_Vol_EM;
    }
  }
{% endmacro %}

{%- macro postOP_FCC(nc,rm_EM,dm,flag_active,regions_CC,init_ht,SIM_MODE,ESC_dict,ECLIQ_dict) %}
{%- set I_PostPrc = {'I_PC':'Omega_PS_currentsource','I_1':'Omega_PS_R_1','I_2':'Omega_PS_R_2', 'I_cpc': 'Omega_PS_R_3', 'I_crowbar': 'Omega_PS_R_crowbar', 'I_c_r': 'Omega_PS_R_c_r', 'I_EE': 'Omega_EE_V_EE', 'I_c': 'Omega_EE_R_c', 'I_s': 'Omega_EE_R_s', 'I_EE_n': 'Omega_EE_V_EE_n', 'I_c_n': 'Omega_EE_R_c_n', 'I_s_n': 'Omega_EE_R_s_n', 'I_C': 'Omega_CLIQ_R' }%} 
{% set I_PostPrc_ADDCOILS = { 'I_EQ': 'Omega_ECLIQ_R_leads', 'I_ESC': 'Omega_ESC_R_leads', 'I_ESC_Diode': 'Omega_ESC_L_Diode', 'I_ESC_C': 'Omega_ESC_R_unit'} %}
{% set U_PostPrc_ESC = ['ESC_C1','ESC_C2','ESC_R_leads','ESC_R_unit','ESC_L','ESC_L_Diode','ESC_Ud_Diode','Omega_ESC_R_switch'] %}
{% set U_PostPrc_ECLIQ = ['ECLIQ_L_leads','ECLIQ_R_leads','ECLIQ_currentsource'] %}
{% set U_PostPrc = U_PostPrc_ECLIQ + U_PostPrc_ESC %}
{% if SIM_MODE == 'Th_Mag' or SIM_MODE == 'Mag_dyn' or SIM_MODE == 'Th_Mag_sta' or SIM_MODE == 'Mag_sta'%}
  { Name circuit_coupling_sta; NameOfPostProcessing MagSta_a_2D ;
    Operation {
      Print[ I_, OnRegion Region[{{% for i in I_PostPrc.keys() if i in dm.magnet.postproc.circuit_coupling.variables_I %}<<I_PostPrc[i]>> {%    endfor %} {% for i in I_PostPrc_ADDCOILS.keys() if i in dm.magnet.postproc.circuit_coupling.variables_I %}{% for j in range(1,ESC_dict["Units"]+1) %} <<I_PostPrc_ADDCOILS[i]~'_'~j>>{% endfor %}{% for j in range(1,ECLIQ_dict["Units"]+1) %} <<I_PostPrc_ADDCOILS[i]~'_'~j>>{% endfor %}{% endfor %}}], File "CC_output/I.csv", Format Table, Comma, AppendToExistingFile 1, SendToServer "No"] ;

      Print[ U_, OnRegion Region[{{% for i in dm.magnet.postproc.circuit_coupling.variables_U if i not in U_PostPrc %} <<'Omega_'~i>>{%    endfor %}{% for i in dm.magnet.postproc.circuit_coupling.variables_U if i in U_PostPrc_ESC %}{% for j in range(1,ESC_dict["Units"]+1) %} <<'Omega_'~i~'_'~j>>{% endfor %}{%    endfor %}{% for i in dm.magnet.postproc.circuit_coupling.variables_U if i in U_PostPrc_ECLIQ %}{% for j in range(1,ECLIQ_dict["Units"]+1) %} <<'Omega_'~i~'_'~j>>{% endfor %}{%    endfor %}}] , File "CC_output/U.csv", Format Table, Comma, AppendToExistingFile 1, SendToServer "No"] ;

      Print[ I_mag, OnRegion <<nc.omega>><<nc.powered>>_EM, File "CC_output/I_mag.csv", Format Table, Comma, SendToServer "No", AppendToExistingFile 1] ;
      Print[ U_mag, OnRegion <<nc.omega>><<nc.powered>>_EM , File "CC_output/U_mag.csv", Format Table, Comma, SendToServer "No", AppendToExistingFile 1] ;
    }
  }
  {% endif %}
  {% if SIM_MODE != 'Th_Mag_sta' and SIM_MODE != 'Mag_sta'%}
    { Name circuit_coupling; NameOfPostProcessing MagDyn_a_2D;
    Operation {

      Print[ I_, OnRegion Region[{{% for i in I_PostPrc.keys() if i in dm.magnet.postproc.circuit_coupling.variables_I %}<<I_PostPrc[i]>> {%    endfor %} {% for i in I_PostPrc_ADDCOILS.keys() if i in dm.magnet.postproc.circuit_coupling.variables_I %}{% for j in range(1,ESC_dict["Units"]+1) %} <<I_PostPrc_ADDCOILS[i]~'_'~j>>{% endfor %}{% for j in range(1,ECLIQ_dict["Units"]+1) %} <<I_PostPrc_ADDCOILS[i]~'_'~j>>{% endfor %}{% endfor %}}], File "CC_output/I.csv", Format Table, Comma, AppendToExistingFile 1, SendToServer "No"] ;

      Print[ U_, OnRegion Region[{{% for i in dm.magnet.postproc.circuit_coupling.variables_U if i not in U_PostPrc %} <<'Omega_'~i>>{%    endfor %}{% for i in dm.magnet.postproc.circuit_coupling.variables_U if i in U_PostPrc_ESC %}{% for j in range(1,ESC_dict["Units"]+1) %} <<'Omega_'~i~'_'~j>>{% endfor %}{%    endfor %}{% for i in dm.magnet.postproc.circuit_coupling.variables_U if i in U_PostPrc_ECLIQ %}{% for j in range(1,ECLIQ_dict["Units"]+1) %} <<'Omega_'~i~'_'~j>>{% endfor %}{%    endfor %}}] , File "CC_output/U.csv", Format Table, Comma, AppendToExistingFile 1, SendToServer "No"] ;

      Print[ I_mag, OnRegion <<nc.omega>><<nc.powered>>_EM, File "CC_output/I_mag.csv", Format Table, Comma, SendToServer "No", AppendToExistingFile 1] ;
      Print[ U_mag, OnRegion <<nc.omega>><<nc.powered>>_EM , File "CC_output/U_mag.csv", Format Table, Comma, SendToServer "No", AppendToExistingFile 1] ;
    }
  }
  {% endif %}
{% endmacro %}