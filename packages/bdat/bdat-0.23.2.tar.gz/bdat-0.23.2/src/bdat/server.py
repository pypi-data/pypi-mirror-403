import io
import json

from flask import Flask, Response, render_template, request, send_file, url_for

import bdat.functions
from bdat import entities
from bdat.database.storage.resource_id import ResourceId
from bdat.database.storage.resource_param import ResourceIdParam
from bdat.database.storage.storage import Storage
from bdat.plots.plot import plotfunctions

storage: Storage

app = Flask(
    "bdat",
    static_folder="../../altair",
    static_url_path="/static",
    template_folder="../../altair/template",
)


@app.route("/plot/<resource_id>", methods=["GET"])
def show_plot(resource_id):
    return render_template(
        "plot.html",
        chart_script=url_for("get_script", resource_id=resource_id),
    )


@app.route("/script/<resource_id>", methods=["GET"])
def get_script(resource_id, chart_url=None):
    chart_url = request.args.get("chart_url", chart_url)
    if chart_url is None:
        plot_id = ResourceIdParam(entities.plots.Plotdata).convert(
            resource_id, None, None
        )
        plottype = request.args.get("plottype", None)
        if plottype is None:
            plotdata = storage.get_as_doc(plot_id)
            plottype = plotdata["plottype"]
        data_endpoint = request.args.get("data_endpoint", None)
        if data_endpoint is None:
            data_endpoint = "get_plotdata"
        chart_url = f"/static/out/{plottype}.json"
        quoted_data_url = (
            "'" + url_for(data_endpoint, resource_id=resource_id, dataset="") + "'"
        )
        # script = f"const chartspec_url = '/static/out/{plottype}.json';\n"
        # script += f"const data_url = '{url_for(data_endpoint, resource_id=resource_id, dataset='')}';\n"
    else:
        quoted_data_url = "null"
        # script = f"const chartspec_url = '{chart_url}';\n"
        # script += f"const data_url = null;\n"
    embedTarget = request.args.get("target", "#vis")
    # script += f"const target = '{embedTarget}';\n"
    script = """
        async function insertDataUrl(spec, data_url) {
            for (var k in spec) {
                if (k === 'data' && 'url' in spec[k]) {
                    spec[k].url = data_url + spec[k].url;
                }
                if (spec[k] && typeof spec[k] === 'object') {
                    spec[k] = await insertDataUrl(spec[k], data_url);
                }
            }
            return spec;
        }

        async function showChart(spec, data_url, target) {
            if (data_url != null) {
                spec = await insertDataUrl(spec, data_url);
            }
            var opt = { "renderer": "canvas", "actions": true, "target": "_blank" };
            vegaEmbed(target, spec, opt);
        }

    """
    script += f"fetch('{chart_url}').then(res => res.json()).then(spec => showChart(spec, {quoted_data_url}, '{embedTarget}'));"
    return Response(script, mimetype="application/javascript")


@app.route("/data/plot/<resource_id>/<dataset>", methods=["GET"])
def get_plotdata(resource_id, dataset):
    plot_id = ResourceIdParam(entities.plots.Plotdata).convert(resource_id, None, None)
    return send_file(
        storage.get_file(plot_id, dataset),
        mimetype="application/json",
        download_name=dataset if dataset else "example.json",
    )


@app.route("/stepsplot/<resource_id>", methods=["GET"])
def get_stepsplot(resource_id):
    return render_template(
        "plot.html",
        chart_script=url_for(
            "get_script",
            resource_id=resource_id,
            plottype="steps",
            data_endpoint="get_stepsdata",
        ),
    )


@app.route("/data/steps/<resource_id>/<dataset>", methods=["GET"])
def get_stepsdata(resource_id, dataset):
    test_id = ResourceIdParam(entities.test.Test).convert(resource_id, None, None)
    steps = bdat.functions.steps(storage, test_id)
    plot = bdat.functions.plot(storage, steps, "steps")
    return plot.data[dataset]


@app.route("/steps/<resource_id>", methods=["GET"])
def get_steps(resource_id):
    group_id = ResourceIdParam(entities.group.TestGroup).convert(
        resource_id, None, None
    )
    group = storage.get_as_doc(group_id)
    return render_template(
        "plotgroup.html",
        plot_url=url_for("get_stepsplot", resource_id=""),
        items=group["tests"],
    )


@app.get("/testeval/<resource_id>")
def get_testeval(resource_id):
    testeval_id = ResourceIdParam(entities.TestEval).convert(resource_id, None, None)
    testeval = storage.get_or_raise(testeval_id)
    plots = {
        "testeval": url_for(
            "get_script",
            resource_id=resource_id,
            plottype="testevals",
            target="#testeval",
        ),
        "details": url_for(
            "get_script",
            chart_url=url_for(
                "get_plotspec", resource_id=resource_id, plottype="testeval_details"
            ),
            resource_id=resource_id,
            plottype="testevals",
            target="#details",
        ),
    }

    return render_template(
        "testeval.html",
        testeval=testeval,
        plots=plots,
    )


@app.get("/plot/spec/<resource_id>/<plottype>")
def get_plotspec(resource_id, plottype):
    plot_function = plotfunctions[plottype]
    resource = storage.get_or_raise(ResourceId.from_str(resource_id, entities.Entity))
    plotdata = plot_function(storage, resource)
    buffer = io.BytesIO()
    # json.dump(plotdata.plot, buffer)
    # buffer.seek(0)
    # return send_file(buffer, mimetype="application/json")
    return plotdata.plot
