from flask import Flask, request, jsonify
from dataLoader import dataLoader

app = Flask(__name__)

myDataLoader = dataLoader()


@app.route('/api/v1/all_states', methods=['GET'])
def api_list_states():
    return (jsonify(myDataLoader.all_states()))


@app.route('/api/v1/all_counties', methods=['GET'])
def api_list_counties():
    return (jsonify(myDataLoader.all_counties()))


@app.route('/api/v1/cases/<states>', methods=['GET'])
def api_get_states(states):
    state_list = states.split('+')
    return (jsonify(
        myDataLoader.get_data(state_list,
                              cases=True).to_dict(orient='records')))


if __name__ == "__main__":
    app.debug = True
    app.run(debug=True)
    #app.run() #run app