from flask import Flask, request, jsonify, Blueprint
from dataLoader import dataLoader
from api_config import api_key

app = Flask(__name__)

bp = Blueprint('api', __name__, template_folder='templates')

#app.config["APPLICATION_ROOT"] =
myDataLoader = dataLoader()


@bp.route(f'/api/v1/{api_key}/all_states', methods=['GET'])
def api_list_states():
    return (jsonify(myDataLoader.all_states()))


@bp.route(f'/api/v1/{api_key}/all_counties', methods=['GET'])
def api_list_counties():
    return (jsonify(myDataLoader.all_counties()))


@bp.route(f'/api/v1/{api_key}/cases/<states>', methods=['GET'])
def api_get_states(states):
    state_list = states.split('+')
    return (jsonify(
        myDataLoader.get_data(state_list,
                              cases=True).to_dict(orient='records')))


app.register_blueprint(
    bp,
    url_prefix="/covid_api",
)

if __name__ == "__main__":
    app.debug = True
    app.run(debug=True)
    #app.run() #run app