import streamlit as st
import pandas as pd
import networkx as nx
import folium
from streamlit_folium import folium_static
from geopy.distance import geodesic
import numpy as np
import os
from folium import plugins

# Set page config
st.set_page_config(
    page_title="Disaster Management System",
    page_icon="🚨",
    layout="wide"
)

# Add Emergency Contacts Data
EMERGENCY_CONTACTS = {
    "Police Control Room": {
        "number": "112",
        "address": "Police Headquarters, Dehradun",
        "available": "24/7"
    },
    "Fire Emergency": {
        "number": "101",
        "address": "Fire Station HQ, Dehradun",
        "available": "24/7"
    },
    "Ambulance Services": {
        "number": "108",
        "address": "Emergency Medical Services, Dehradun",
        "available": "24/7"
    },
    "Disaster Management Authority": {
        "number": "1070",
        "address": "State Emergency Operations Center, Dehradun",
        "available": "24/7"
    },
    "NDRF Control Room": {
        "number": "011-24363260",
        "address": "National Disaster Response Force, Dehradun",
        "available": "24/7"
    },
    "Max Super Specialty Hospital": {
        "number": "+91-135-6673000",
        "address": "Max Hospital, Dehradun",
        "available": "24/7"
    },
    "GEIMS Hospital": {
        "number": "+91-135-1234567",
        "address": "GEIMS Hospital, Dehradun",
        "available": "24/7"
    },
    "Blood Bank": {
        "number": "+91-135-2750750",
        "address": "Blood Bank, GEIMS Hospital",
        "available": "24/7"
    },
    "District Control Room": {
        "number": "+91-135-2726066",
        "address": "District Collectorate, Dehradun",
        "available": "24/7"
    },
    "Red Cross Society": {
        "number": "+91-135-2657014",
        "address": "Red Cross Bhawan, Dehradun",
        "available": "8 AM - 8 PM"
    }
}

# Load data with error handling
def load_data():
    try:
        nodes_df = pd.read_csv('nodes.txt')
        edges_df = pd.read_csv('edges.txt')
        supplies_df = pd.read_csv('relief_supplies.txt')
        
        # Create a pivot table for supplies to make it easier to work with
        supplies_pivot = supplies_df.pivot_table(
            index='Location',
            columns='Supply_Type',
            values=['Stock_Level', 'Vehicle_Capacity'],
            aggfunc={'Stock_Level': 'first', 'Vehicle_Capacity': 'first'}
        ).reset_index()
        
        # Flatten column names
        supplies_pivot.columns = [f"{col[0]}_{col[1]}" if col[1] else col[0] for col in supplies_pivot.columns]
        
        return nodes_df, edges_df, supplies_df, supplies_pivot
    except Exception as e:
        st.error("Error loading data files. Please check if all required files exist.")
        return None, None, None, None

def get_location_supplies(supplies_pivot, location_id):
    """Get formatted supplies information for a location"""
    if location_id not in supplies_pivot['Location'].values:
        return None
    
    supplies = supplies_pivot[supplies_pivot['Location'] == location_id].iloc[0]
    return {
        'Water': {
            'stock': supplies['Stock_Level_Water'],
            'capacity': supplies['Vehicle_Capacity_Water']
        },
        'Food': {
            'stock': supplies['Stock_Level_Food'],
            'capacity': supplies['Vehicle_Capacity_Food']
        },
        'Medicine': {
            'stock': supplies['Stock_Level_Medicine'],
            'capacity': supplies['Vehicle_Capacity_Medicine']
        }
    }

# Create graph for pathfinding
def create_graph(nodes_df, edges_df):
    try:
        G = nx.Graph()
        
        # Add nodes with their attributes
        for _, row in nodes_df.iterrows():
            G.add_node(row['ID'], 
                      pos=(row['Latitude'], row['Longitude']),
                      name=row['Name'],
                      type=row['Type'],
                      capacity=row['Capacity'],
                      demand=row['Demand'])
        
        # Add edges with travel time and distance
        for _, row in edges_df.iterrows():
            G.add_edge(row['From'], row['To'], 
                      weight=row['Travel_Time_min'],
                      distance=row['Distance_km'],
                      condition=row['Road_Condition'])
        return G
    except Exception as e:
        st.error("Error creating network graph.")
        return None

# Find nearest facilities with path information
def find_nearest_facilities(G, start_node, facility_type):
    try:
        facilities = [(node, data) for node, data in G.nodes(data=True) 
                     if data.get('type') == facility_type]
        
        if not facilities:
            return None, float('inf'), []
        
        nearest = None
        min_time = float('inf')
        best_path = []
        
        for facility, _ in facilities:
            try:
                path = nx.shortest_path(G, start_node, facility, weight='weight')
                time = sum(G[path[i]][path[i+1]]['weight'] for i in range(len(path)-1))
                if time < min_time:
                    min_time = time
                    nearest = facility
                    best_path = path
            except nx.NetworkXNoPath:
                continue
        
        return nearest, min_time, best_path
    except Exception as e:
        return None, float('inf'), []

def distribute_hospital_demands(nodes_df, G):
    """Distribute demands from affected areas to nearby hospitals based on proximity and capacity"""
    # Get affected areas and hospitals
    affected_areas = nodes_df[nodes_df['Type'] == 'affected_area'].copy()
    hospitals = nodes_df[nodes_df['Type'] == 'hospital'].copy()
    
    # Create a dictionary to store hospital assignments
    hospital_assignments = {hospital['ID']: [] for _, hospital in hospitals.iterrows()}
    updated_demands = {hospital['ID']: 0 for _, hospital in hospitals.iterrows()}
    
    # For each affected area, distribute demand to nearest hospitals
    for _, area in affected_areas.iterrows():
        if area['Demand'] > 0:
            area_demand = area['Demand']
            hospital_distances = []
            
            # Calculate distances to all hospitals
            for _, hospital in hospitals.iterrows():
                try:
                    path = nx.shortest_path(G, area['ID'], hospital['ID'], weight='weight')
                    travel_time = sum(G[path[i]][path[i+1]]['weight'] for i in range(len(path)-1))
                    available_capacity = hospital['Capacity'] - updated_demands[hospital['ID']]
                    
                    if available_capacity > 0:
                        hospital_distances.append({
                            'hospital_id': hospital['ID'],
                            'travel_time': travel_time,
                            'available_capacity': available_capacity
                        })
                except nx.NetworkXNoPath:
                    continue
            
            # Sort hospitals by travel time
            hospital_distances.sort(key=lambda x: x['travel_time'])
            
            # Distribute demand among hospitals
            remaining_demand = area_demand
            for hospital in hospital_distances:
                if remaining_demand <= 0:
                    break
                    
                assignable_demand = min(remaining_demand, hospital['available_capacity'])
                if assignable_demand > 0:
                    hospital_assignments[hospital['hospital_id']].append({
                        'area_id': area['ID'],
                        'area_name': area['Name'],
                        'assigned_demand': assignable_demand,
                        'travel_time': hospital['travel_time']
                    })
                    updated_demands[hospital['hospital_id']] += assignable_demand
                    remaining_demand -= assignable_demand
    
    return hospital_assignments, updated_demands

def create_route_map(nodes_df, start_node, end_node, path, map_center=[30.3165, 78.0322]):
    """Create a map with route visualization"""
    m = folium.Map(location=map_center, zoom_start=12)
    
    # Add markers for start and end points
    start_info = nodes_df[nodes_df['ID'] == start_node].iloc[0]
    end_info = nodes_df[nodes_df['ID'] == end_node].iloc[0]
    
    # Add start marker (affected area)
    folium.Marker(
        [start_info['Latitude'], start_info['Longitude']],
        popup=f"<b>Start: {start_info['Name']}</b>",
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)
    
    # Add end marker (facility)
    end_color = 'green' if end_info['Type'] == 'shelter' else 'blue' if end_info['Type'] == 'hospital' else 'orange'
    folium.Marker(
        [end_info['Latitude'], end_info['Longitude']],
        popup=f"<b>Destination: {end_info['Name']}</b>",
        icon=folium.Icon(color=end_color, icon='info-sign')
    ).add_to(m)
    
    # Create route coordinates
    route_coords = []
    for node_id in path:
        node = nodes_df[nodes_df['ID'] == node_id].iloc[0]
        route_coords.append([node['Latitude'], node['Longitude']])
    
    # Add the route line
    folium.PolyLine(
        route_coords,
        weight=3,
        color='red',
        opacity=0.8
    ).add_to(m)
    
    return m

def get_path_description(nodes_df, path):
    """Get a human-readable description of the path"""
    route_desc = []
    for i, node_id in enumerate(path):
        node = nodes_df[nodes_df['ID'] == node_id].iloc[0]
        if i == 0:
            route_desc.append(f"Start at {node['Name']}")
        elif i == len(path) - 1:
            route_desc.append(f"Arrive at {node['Name']}")
        else:
            route_desc.append(f"Continue through {node['Name']}")
    return route_desc

def allocate_rescue_teams(G, nodes_df, rescue_teams_df, disaster_zones_df):
    """Allocate rescue teams to disaster zones based on proximity"""
    # Get unique disaster locations
    disaster_locations = disaster_zones_df['Location_ID'].unique()
    
    # Initialize allocation dictionary
    allocations = {}
    available_teams = rescue_teams_df[rescue_teams_df['Availability'] == 'Available'].copy()
    
    # Allocate teams to disaster zones
    for location_id in disaster_locations:
        if len(available_teams) == 0:
            break
            
        # Find nearest available team
        min_time = float('inf')
        best_team = None
        best_path = None
        
        for _, team in available_teams.iterrows():
            try:
                path = nx.shortest_path(G, team['Base_Location'], location_id, weight='weight')
                time = sum(G[path[i]][path[i+1]]['weight'] for i in range(len(path)-1))
                # Adjust time based on team's speed relative to default speed (50 kmph)
                time = time * (50 / team['Speed_kmph'])
                
                if time < min_time:
                    min_time = time
                    best_team = team
                    best_path = path
            except nx.NetworkXNoPath:
                continue
        
        if best_team is not None:
            # Get severity level for this location
            severity = disaster_zones_df[disaster_zones_df['Location_ID'] == location_id]['Severity_Level'].max()
            
            allocations[location_id] = {
                'team_id': best_team['Team_ID'],
                'severity': severity,
                'estimated_time': min_time,
                'path': best_path,
                'base_location': best_team['Base_Location'],
                'speed': best_team['Speed_kmph']
            }
            # Remove allocated team from available teams
            available_teams = available_teams[available_teams['Team_ID'] != best_team['Team_ID']]
    
    return allocations

def load_rescue_data():
    try:
        rescue_teams_df = pd.read_csv('rescue_teams.txt')
        disaster_zones_df = pd.read_csv('disaster_zones.txt')
        return rescue_teams_df, disaster_zones_df
    except Exception as e:
        st.error("Error loading rescue data files.")
        return None, None

# Load data
nodes_df, edges_df, supplies_df, supplies_pivot = load_data()
rescue_teams_df, disaster_zones_df = load_rescue_data()

if all(v is not None for v in [nodes_df, edges_df, supplies_df, supplies_pivot, rescue_teams_df, disaster_zones_df]):
    G = create_graph(nodes_df, edges_df)
    
    if G is not None:
        # Create tabs for main dashboard and emergency contacts
        tab1, tab2, tab3 = st.tabs(["📊 Main Dashboard", "🚑 Rescue Teams", "☎️ Emergency Contacts"])
        
        with tab1:
            st.title("🚨 Disaster Management Dashboard")
            
            # Create two columns
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("Disaster Zone Map")
                m = folium.Map(location=[30.3165, 78.0322], zoom_start=12)
                
                # Add markers for all nodes with custom icons and colors
                for _, row in nodes_df.iterrows():
                    color = 'red' if row['Type'] == 'affected_area' else \
                            'green' if row['Type'] == 'shelter' else \
                            'blue' if row['Type'] == 'hospital' else \
                            'orange' if row['Type'] == 'warehouse' else 'gray'
                    
                    # Get supplies for this location
                    supplies = get_location_supplies(supplies_pivot, row['ID'])
                    
                    popup_text = f"""
                    <b>{row['Name']}</b><br>
                    Type: {row['Type']}<br>
                    """
                    if row['Type'] in ['shelter', 'hospital']:
                        popup_text += f"Capacity: {row['Capacity']}<br>"
                    if row['Demand'] > 0:
                        popup_text += f"Current Demand: {row['Demand']}<br>"
                    if supplies:
                        popup_text += "<br>Available Supplies:<br>"
                        for supply_type in ['Water', 'Food', 'Medicine']:
                            popup_text += f"- {supply_type}: {supplies[supply_type]['stock']:,} units<br>"
                    
                    folium.Marker(
                        [row['Latitude'], row['Longitude']],
                        popup=popup_text,
                        icon=folium.Icon(color=color)
                    ).add_to(m)
                
                # Add rescue team base locations as purple markers
                if rescue_teams_df is not None:
                    for _, team in rescue_teams_df.iterrows():
                        base_node = nodes_df[nodes_df['ID'] == team['Base_Location']]
                        if not base_node.empty:
                            lat = base_node['Latitude'].iloc[0]
                            lon = base_node['Longitude'].iloc[0]
                            folium.Marker(
                                [lat, lon],
                                popup=f"<b>Rescue Team {team['Team_ID']}</b><br>Speed: {team['Speed_kmph']} km/h<br>Status: {team['Availability']}",
                                icon=folium.Icon(color='purple', icon='user', prefix='fa')
                            ).add_to(m)
                
                folium_static(m)
            
            with col2:
                st.subheader("Emergency Response Calculator")
                
                # Create a dropdown for selecting affected area
                affected_areas = nodes_df[nodes_df['Type'] == 'affected_area']
                selected_area = st.selectbox(
                    "Select Affected Area",
                    affected_areas['ID'].tolist(),
                    format_func=lambda x: f"{nodes_df[nodes_df['ID'] == x]['Name'].iloc[0]} (Demand: {nodes_df[nodes_df['ID'] == x]['Demand'].iloc[0]})"
                )
                
                if selected_area:
                    st.write("---")
                    
                    # Find nearest shelter
                    nearest_shelter, shelter_time, shelter_path = find_nearest_facilities(G, selected_area, 'shelter')
                    if nearest_shelter:
                        shelter_info = nodes_df[nodes_df['ID'] == nearest_shelter].iloc[0]
                        shelter_supplies = get_location_supplies(supplies_pivot, nearest_shelter)
                        
                        st.info(f"📍 Nearest Shelter: {shelter_info['Name']}")
                        st.write(f"Travel Time: {shelter_time:.1f} minutes")
                        st.write(f"Available Capacity: {shelter_info['Capacity'] - shelter_info['Demand']} people")
                        
                        # Show route description
                        st.write("---")
                        st.write("📝 Route to Nearest Shelter")
                        route_steps = get_path_description(nodes_df, shelter_path)
                        for i, step in enumerate(route_steps, 1):
                            st.write(f"{i}. {step}")
                        
                        if shelter_supplies:
                            st.write("Available Supplies at Shelter:")
                            for supply_type in ['Water', 'Food', 'Medicine']:
                                st.write(
                                    f"- {supply_type}: {shelter_supplies[supply_type]['stock']:,} units "
                                    f"(Vehicle Capacity: {shelter_supplies[supply_type]['capacity']})"
                                )
                    
                    st.write("---")
                    
                    # Find nearest hospital with route description
                    nearest_hospital, hospital_time, hospital_path = find_nearest_facilities(G, selected_area, 'hospital')
                    if nearest_hospital:
                        hospital_info = nodes_df[nodes_df['ID'] == nearest_hospital].iloc[0]
                        hospital_supplies = get_location_supplies(supplies_pivot, nearest_hospital)
                        
                        st.info(f"🏥 Nearest Hospital: {hospital_info['Name']}")
                        st.write(f"Travel Time: {hospital_time:.1f} minutes")
                        st.write(f"Available Beds: {hospital_info['Capacity'] - hospital_info['Demand']}")
                        
                        # Show route description
                        st.write("---")
                        st.write("📝 Route to Nearest Hospital")
                        route_steps = get_path_description(nodes_df, hospital_path)
                        for i, step in enumerate(route_steps, 1):
                            st.write(f"{i}. {step}")
                        
                        if hospital_supplies:
                            st.write("Medical Supplies at Hospital:")
                            for supply_type in ['Water', 'Food', 'Medicine']:
                                st.write(
                                    f"- {supply_type}: {hospital_supplies[supply_type]['stock']:,} units "
                                    f"(Vehicle Capacity: {hospital_supplies[supply_type]['capacity']})"
                                )
                    
                    st.write("---")
                    
                    # Find nearest warehouse
                    nearest_warehouse, warehouse_time, warehouse_path = find_nearest_facilities(G, selected_area, 'warehouse')
                    if nearest_warehouse:
                        warehouse_info = nodes_df[nodes_df['ID'] == nearest_warehouse].iloc[0]
                        warehouse_supplies = get_location_supplies(supplies_pivot, nearest_warehouse)
                        
                        st.info(f"📦 Nearest Warehouse: {warehouse_info['Name']}")
                        st.write(f"Travel Time: {warehouse_time:.1f} minutes")
                        
                        if warehouse_supplies:
                            st.write("Available Supplies at Warehouse:")
                            for supply_type in ['Water', 'Food', 'Medicine']:
                                st.write(
                                    f"- {supply_type}: {warehouse_supplies[supply_type]['stock']:,} units "
                                    f"(Vehicle Capacity: {warehouse_supplies[supply_type]['capacity']})"
                                )

            # Additional Statistics
            st.write("---")
            col1, col2, col3 = st.columns(3)

            with col1:
                total_shelters = len(nodes_df[nodes_df['Type'] == 'shelter'])
                available_shelter_capacity = (nodes_df[nodes_df['Type'] == 'shelter']['Capacity'] - 
                                           nodes_df[nodes_df['Type'] == 'shelter']['Demand']).sum()
                st.metric("Total Shelters", total_shelters)
                st.metric("Available Shelter Capacity", available_shelter_capacity)
                st.metric("Total Shelter Demand", nodes_df[nodes_df['Type'] == 'shelter']['Demand'].sum())

            with col2:
                # Calculate hospital assignments
                hospital_assignments, updated_demands = distribute_hospital_demands(nodes_df, G)
                
                total_hospitals = len(nodes_df[nodes_df['Type'] == 'hospital'])
                total_hospital_capacity = nodes_df[nodes_df['Type'] == 'hospital']['Capacity'].sum()
                total_hospital_demand = sum(updated_demands.values())
                
                st.metric("Total Hospitals", total_hospitals)
                st.metric("Total Hospital Capacity", total_hospital_capacity)
                st.metric("Current Hospital Demand", total_hospital_demand)
                
                # Add hospital demand distribution details
                st.write("---")
                st.subheader("🏥 Hospital Demand Distribution")
                
                hospitals = nodes_df[nodes_df['Type'] == 'hospital']
                for _, hospital in hospitals.iterrows():
                    with st.expander(f"{hospital['Name']} Details"):
                        current_demand = updated_demands[hospital['ID']]
                        available_capacity = hospital['Capacity'] - current_demand
                        
                        st.write(f"**Capacity**: {hospital['Capacity']} beds")
                        st.write(f"**Current Demand**: {current_demand} patients")
                        st.write(f"**Available Beds**: {available_capacity}")
                        
                        if hospital_assignments[hospital['ID']]:
                            st.write("\n**Assigned Patients from Areas:**")
                            for assignment in hospital_assignments[hospital['ID']]:
                                st.write(f"- {assignment['area_name']}: {assignment['assigned_demand']} patients")
                                st.write(f"  Travel time: {assignment['travel_time']:.1f} minutes")
                        else:
                            st.write("\n*No patients currently assigned*")

            with col3:
                # Calculate total supplies by type
                total_water = supplies_df[supplies_df['Supply_Type'] == 'Water']['Stock_Level'].sum()
                total_food = supplies_df[supplies_df['Supply_Type'] == 'Food']['Stock_Level'].sum()
                total_medicine = supplies_df[supplies_df['Supply_Type'] == 'Medicine']['Stock_Level'].sum()
                
                total_warehouses = len(nodes_df[nodes_df['Type'] == 'warehouse'])
                st.metric("Total Warehouses", total_warehouses)
                st.write("Total Available Supplies:")
                st.write(f"- Water: {total_water:,} units")
                st.write(f"- Food: {total_food:,} units")
                st.write(f"- Medicine: {total_medicine:,} units")

            # Show supplies distribution by facility type
            st.write("---")
            st.subheader("Relief Supplies Distribution")
            
            facility_types = ['Shelter', 'Hospital', 'Warehouse']
            supply_types = ['Water', 'Food', 'Medicine']
            
            distribution_data = []
            for facility_type in facility_types:
                locations = nodes_df[nodes_df['Type'].str.lower() == facility_type.lower()]['ID'].tolist()
                facility_supplies = supplies_df[supplies_df['Location'].isin(locations)]
                
                for supply_type in supply_types:
                    total = facility_supplies[facility_supplies['Supply_Type'] == supply_type]['Stock_Level'].sum()
                    distribution_data.append({
                        'Facility Type': facility_type,
                        'Supply Type': supply_type,
                        'Total Stock': total
                    })
            
            distribution_df = pd.DataFrame(distribution_data)
            distribution_pivot = distribution_df.pivot(
                index='Facility Type',
                columns='Supply Type',
                values='Total Stock'
            ).reset_index()
            
            st.dataframe(distribution_pivot, hide_index=True)

        with tab2:
            st.title("🚑 Rescue Team Allocation")
            
            # Interactive selection of disaster zone
            disaster_zone_options = disaster_zones_df['Location_ID'].unique().tolist()
            selected_zone = st.selectbox(
                "Select Disaster Zone to Allocate Rescue Team",
                disaster_zone_options,
                format_func=lambda x: nodes_df[nodes_df['ID'] == x]['Name'].iloc[0] if not nodes_df[nodes_df['ID'] == x].empty else x
            )
            
            # Allocate rescue team for the selected disaster zone only
            def allocate_for_zone(G, nodes_df, rescue_teams_df, zone_id):
                available_teams = rescue_teams_df[rescue_teams_df['Availability'] == 'Available'].copy()
                min_time = float('inf')
                best_team = None
                best_path = None
                for _, team in available_teams.iterrows():
                    try:
                        path = nx.shortest_path(G, team['Base_Location'], zone_id, weight='weight')
                        time = sum(G[path[i]][path[i+1]]['weight'] for i in range(len(path)-1))
                        time = time * (50 / team['Speed_kmph'])
                        if time < min_time:
                            min_time = time
                            best_team = team
                            best_path = path
                    except nx.NetworkXNoPath:
                        continue
                if best_team is not None:
                    severity = disaster_zones_df[disaster_zones_df['Location_ID'] == zone_id]['Severity_Level'].max()
                    return {
                        'team_id': best_team['Team_ID'],
                        'severity': severity,
                        'estimated_time': min_time,
                        'path': best_path,
                        'base_location': best_team['Base_Location'],
                        'speed': best_team['Speed_kmph']
                    }
                else:
                    return None
            
            allocation = allocate_for_zone(G, nodes_df, rescue_teams_df, selected_zone)
            
            if allocation:
                location_name = nodes_df[nodes_df['ID'] == selected_zone]['Name'].iloc[0]
                base_location_name = nodes_df[nodes_df['ID'] == allocation['base_location']]['Name'].iloc[0]
                st.subheader(f"Team {allocation['team_id']} → {location_name} (Severity {allocation['severity']})")
                st.write(f"**Base Location:** {base_location_name}")
                st.write(f"**Team Speed:** {allocation['speed']} km/h")
                st.write(f"**Estimated Arrival Time to Disaster Zone:** {allocation['estimated_time']:.1f} minutes")
                st.write("**Route to Disaster Zone:**")
                route_steps = get_path_description(nodes_df, allocation['path'])
                for i, step in enumerate(route_steps, 1):
                    st.write(f"{i}. {step}")
                st.write("\n**Required Resources at Disaster Zone:**")
                location_resources = disaster_zones_df[disaster_zones_df['Location_ID'] == selected_zone]
                for _, resource in location_resources.iterrows():
                    st.write(f"- {resource['Resource_Type']}: {resource['Amount']} units")
                # After reaching disaster zone, go to nearest available shelter
                nearest_shelter, shelter_time, shelter_path = find_nearest_facilities(G, selected_zone, 'shelter')
                if nearest_shelter:
                    shelter_name = nodes_df[nodes_df['ID'] == nearest_shelter]['Name'].iloc[0]
                    st.write("\n---")
                    st.write(f"**Next Step: Proceed to Nearest Shelter ({shelter_name})**")
                    st.write(f"Estimated Travel Time: {shelter_time:.1f} minutes")
                    st.write("**Route to Shelter:**")
                    shelter_route_steps = get_path_description(nodes_df, shelter_path)
                    for i, step in enumerate(shelter_route_steps, 1):
                        st.write(f"{i}. {step}")
            else:
                st.warning("No available rescue team for this disaster zone.")

        with tab3:
            st.title("☎️ Emergency Contacts")
            
            # Create single column for emergency contacts
            st.subheader("🚓 Emergency Services")
            st.info("""
            **General Emergency**: 112
            **Ambulance**: 108
            **Fire**: 101
            **Disaster Helpline**: 1070
            """)
            
            # Display emergency contacts in a structured way
            st.subheader("📞 Important Contact Numbers")
            for service, details in EMERGENCY_CONTACTS.items():
                with st.expander(f"{service}"):
                    st.write(f"**Phone**: {details['number']}")
                    st.write(f"**Address**: {details['address']}")
                    st.write(f"**Availability**: {details['available']}")

            # Add a map showing all emergency facilities
            st.subheader("🗺️ Emergency Facilities Map")
            emergency_map = folium.Map(location=[30.3165, 78.0322], zoom_start=12)
            
            # Add markers for hospitals and emergency services
            for _, facility in nodes_df[nodes_df['Type'] == 'hospital'].iterrows():
                folium.Marker(
                    [facility['Latitude'], facility['Longitude']],
                    popup=f"""
                    <b>{facility['Name']}</b><br>
                    Type: Hospital<br>
                    Capacity: {facility['Capacity']} beds<br>
                    Available: {facility['Capacity'] - facility['Demand']} beds
                    """,
                    icon=folium.Icon(color='red', icon='plus', prefix='fa')
                ).add_to(emergency_map)
            
            folium_static(emergency_map)
            
            # Emergency Guidelines
            st.write("---")
            st.subheader("🚨 Emergency Guidelines")
            
            with st.expander("In Case of Emergency"):
                st.write("""
                1. Stay calm and assess the situation
                2. Call the appropriate emergency number
                3. Provide clear location and incident details
                4. Follow instructions from emergency personnel
                5. Help others if it's safe to do so
                """)
            
            with st.expander("Disaster Preparedness"):
                st.write("""
                1. Keep emergency contacts handy
                2. Have an emergency kit ready
                3. Know your evacuation routes
                4. Keep important documents in a safe place
                5. Stay informed about weather and emergency alerts
                """)

            with st.expander("Emergency Kit Checklist"):
                st.write("""
                - First aid supplies
                - Flashlight and batteries
                - Important documents
                - Non-perishable food
                - Water (1 gallon per person per day)
                - Battery-powered radio
                - Essential medications
                - Emergency cash
                - Basic tools
                """)

            # Download Emergency Contacts
            st.write("---")
            st.subheader("📱 Save Emergency Contacts")
            
            # Create a downloadable version of emergency contacts
            emergency_contacts_text = "EMERGENCY CONTACTS\n\n"
            for service, details in EMERGENCY_CONTACTS.items():
                emergency_contacts_text += f"{service}:\n"
                emergency_contacts_text += f"Phone: {details['number']}\n"
                emergency_contacts_text += f"Address: {details['address']}\n"
                emergency_contacts_text += f"Available: {details['available']}\n\n"
            
            st.download_button(
                label="Download Emergency Contacts",
                data=emergency_contacts_text,
                file_name="emergency_contacts.txt",
                mime="text/plain"
            ) 