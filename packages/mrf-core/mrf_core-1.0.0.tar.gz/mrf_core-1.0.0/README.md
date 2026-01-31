# Modular Reasoning Framework (MRF)

MRF is a lightweight, transparent, multi-stage reasoning scaffold for autonomous agents. It provides a decomposable structure built from reusable computational primitives (Transform, Evaluate, Filter, Summarize, Reflect, Inspect, Rewrite) to make agent behavior traceable and reliable.

---

## Why MRF

Autonomous agents fail because:

1. No reasoning structure  
2. No constraint layer  
3. No diagnostics  

MRF introduces explicit stages, bounded operations, and full visibility into how reasoning unfolds.

---

## Features

### • Reusable Operators
Transform  
Evaluate  
Filter  
Summarize  
Reflect  
Inspect  
Rewrite  

### • Multi-Stage Pipeline
Understanding → Planning → Execution → Synthesis → Verification

### • Diagnostics
Stage logs  
Confidence tracking  
Goal alignment  
Failure detection  

### • Security-Relevant Mitigation
MRF is not an alignment system, but adds structure that reduces unbounded behavior, prompt-injection surfaces, and silent drift.

---

## Install

```bash
pip install mrf-core
```

---

## Quick Start

from mrfcore.pipeline import ReasoningPipeline

pipeline = ReasoningPipeline(verbose=True)
result = pipeline.run("Plan a three-step morning routine.")

print(result["answer"])
print(result["confidence"])
print(result["valid"])

---

## Inspecting a Stage

pipeline.inspect_stage(result, "understanding")

---

## Custom Pipeline

from mrfcore.phases import UnderstandingPhase, PlanningPhase, ExecutionPhase
from mrfcore.pipeline import Pipeline

pipeline = Pipeline([
    UnderstandingPhase(),
    PlanningPhase(),
    ExecutionPhase()
])

result = pipeline.run("Help me clean my desk efficiently.")

---

## Project Structure

mrfcore/
    operators/
        base.py
        transform.py
        evaluate.py
        filter.py
        summarize.py
        reflect.py
        inspect.py
        rewrite.py
    engine.py
    pipeline.py
    phases.py
    presets.py
    diagnostics.py
    exceptions.py
examples/
tests/

---

## What MRF Is Not

Not alignment
Not a safety guarantee
Not a sandbox
Not a replacement for secure execution layers
MRF adds structure

---

## Contributing

PRs welcome

---

## License

## License

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

This project is licensed under the **Apache License 2.0**.

Copyright 2026 Ryan Sabouhi

Licensed under the Apache License, Version 2.0 (the “License”);
you may not use this file except in compliance with the License. 

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

You may obtain a copy of the License at:
https://www.apache.org/licenses/LICENSE-2.0

---

## Notice

This software contains original work developed as part of the  
**Modular Reasoning Framework (MRF)** by **Ryan Sabouhi**.  
See the `NOTICE` file for additional attribution details.