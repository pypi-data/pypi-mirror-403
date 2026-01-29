import xara 

elem = 1
node = 1

options = {
    "integrator": {
        "type": "LoadControl",
        "step": 10,
    }
}

model = xara.Model(ndm=3, ndf=6)

analysis = xara.StaticAnalysis(model, loads, options)


for step in analysis.steps():
    state = xara.solve(model, step)
    if state.status != xara.successful:
        raise RuntimeError("Analysis did not complete successfully.")

    state.node(node).solution(dof=None)
    state.node(node).rotation(dof=None)
    state.node(node).reaction(dof=None)
    state.cell(elem).response(key=None, **kwds)
    state.iter.size
    step.size


for state in map(xara.solve, analysis.steps()):
    
    step.time
    state.node(node).solution(dof=None)
    step.node(node).rotation(dof=None)
    step.node(node).reaction(dof=None)
    step.cell(elem).response(key=None, **kwds)
    step.iter.size
    step.size

