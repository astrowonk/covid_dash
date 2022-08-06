from flask import Flask, request, jsonify
from dataLoader import dataLoader
from api_config import api_key

app = Flask(__name__)
app.config["APPLICATION_ROOT"] = "/covid_api"
myDataLoader = dataLoader()


@app.route(f'/api/v1/{api_key}/all_states', methods=['GET'])
def api_list_states():
    return (jsonify(myDataLoader.all_states()))


@app.route(f'/api/v1/{api_key}/all_counties', methods=['GET'])
def api_list_counties():
    return (jsonify(myDataLoader.all_counties()))


@app.route(f'/api/v1/{api_key}/cases/<states>', methods=['GET'])
def api_get_states(states):
    state_list = states.split('+')
    return (jsonify(
        myDataLoader.get_data(state_list,
                              cases=True).to_dict(orient='records')))


if __name__ == "__main__":
    app.debug = True
    app.run(debug=True)
    #app.run() #run app