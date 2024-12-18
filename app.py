from flask import Flask, render_template, request, jsonify, redirect, url_for
from rdflib import Graph, Namespace, Literal, RDF

app = Flask(__name__)

# Load the ontology
g = Graph()
g.parse("set_theory.ttl", format="turtle")

# Define namespaces
SET_NS = Namespace("http://www.example.org/set_theory#")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sets', methods=['GET'])
def get_sets():
    sets = []
    for s in g.subjects(predicate=SET_NS.setName):
        sets.append({
            "name": str(s).split('#')[-1],
            "type": g.value(s, SET_NS.setType),
            "elements": [str(e).split('#')[-1] for e in g.objects(subject=s, predicate=SET_NS.hasElement)]
        })
    return jsonify(sets)

@app.route('/set/<set_name>', methods=['GET'])
def get_set_details(set_name):
    set_uri = SET_NS[set_name]
    elements = []
    for element in g.objects(subject=set_uri, predicate=SET_NS.hasElement):
        elements.append(str(element).split('#')[-1])  # Get the local name
    return jsonify({"set": set_name, "elements": elements})

@app.route('/add_element', methods=['GET', 'POST'])
def add_element():
    if request.method == 'POST':
        set_name = request.form['set_name']
        element_name = request.form['element_name']
        
        # Create a new element and add it to the specified set
        set_uri = SET_NS[set_name]
        new_element_uri = SET_NS[element_name.replace(" ", "_")]  # Replace spaces with underscores
        
        # Add the new element to the graph
        g.add((new_element_uri, RDF.type, SET_NS.Element))
        g.add((new_element_uri, SET_NS.elementName, Literal(element_name)))
        g.add((set_uri, SET_NS.hasElement, new_element_uri))
        
        # Save the updated ontology
        g.serialize(destination="set_theory.ttl", format="turtle")
        
        return redirect(url_for('index'))

    # Get all sets for the dropdown
    sets = []
    for s in g.subjects(predicate=SET_NS.setName):
        sets.append(str(s).split('#')[-1])
    
    return render_template('add_element.html', sets=sets)

@app.route('/add_set', methods=['GET', 'POST'])
def add_set():
    if request.method == 'POST':
        set_name = request.form['set_name']
        set_type = request.form['set_type']
        
        # Create a new set and add it to the graph
        new_set_uri = SET_NS[set_name.replace(" ", "_")]  # Replace spaces with underscores
        
        # Add the new set to the graph
        g.add((new_set_uri, RDF.type, SET_NS.Set))
        g.add((new_set_uri, SET_NS.setName, Literal(set_name)))
        g.add((new_set_uri, SET_NS.setType, Literal(set_type)))
        
        # Save the updated ontology
        g.serialize(destination="set_theory.ttl", format="turtle")
        
        return redirect(url_for('index'))

    return render_template('add_set.html')

@app.route('/set_operation', methods=['GET', 'POST'])
def set_operation_page():
    if request.method == 'POST':
        if 'set1' not in request.form or 'set2' not in request.form or 'operation' not in request.form:
            return jsonify({"error": "Missing data"}), 400

        operation = request.form['operation']
        set1_name = request.form['set1']
        set2_name = request.form['set2']
        
        set1_uri = SET_NS[set1_name]
        set2_uri = SET_NS[set2_name]
        
        # Extract only the actual element names
        elements_set1 = {str(g.value(e, SET_NS.elementName)) for e in g.objects(subject=set1_uri, predicate=SET_NS.hasElement)}
        elements_set2 = {str(g.value(e, SET_NS.elementName)) for e in g.objects(subject=set2_uri, predicate=SET_NS.hasElement)}
        print(elements_set1)
        print(elements_set2)
        # Use sets to ensure uniqueness
        result = set()  # Initialize an empty set for the result
        
        if operation == 'union':
            result = elements_set1.union(elements_set2)
        elif operation == 'intersection':
            result = elements_set1.intersection(elements_set2)
        elif operation == 'difference':
            result = elements_set1.difference(elements_set2)
        elif operation == 'subset':
            is_subset = elements_set1.issubset(elements_set2)
            return jsonify({"is_subset": is_subset})
        print(result)
        return jsonify({
            "result": list(result),  # Convert the set back to a list for JSON serialization
            "set1_elements": list(elements_set1),
            "set2_elements": list(elements_set2)
        })

    # If the request method is GET, render the set operation page with available sets
    sets = []
    for s in g.subjects(predicate=SET_NS.setName):
        sets.append(str(s).split('#')[-1])
    
    return render_template('set_operation.html', sets=sets)

if __name__ == '__main__':
    app.run(debug=True)