# Short Note

- **Implemented:** FastAPI prototype with `GET /readings/latest` (UTC timestamp, `simulated: true`), `POST /readings` for batches, device/profile endpoints, health check, and a small web page for demo. Swagger UI is available at `/docs`.
- **Synthetic data:** readings come from a seeded AR(1) simulator driven by per-device profiles. Every response is labelled simulated and carries a disclaimer; flags are plain threshold checks, not diagnosis.
- **Validation and errors:** Pydantic enforces types, required fields, ranges and rejects unknown fields; all errors (422, 404, 405, 500) share one JSON format.
- **Tests:** 46 pytest tests cover successful responses, invalid input and error cases, simulator repeatability/ranges, and alert boundary values.
- **Incomplete / limitations:** no real data or database; thresholds are not clinically validated; signals are independent; shipped profiles are starter values until `scripts/build_profiles.py` is run on CTU-UHB.
- **Next improvements:** coupled signals and realistic events (e.g. contractions), a stateful stream so "latest" continues smoothly, configurable thresholds, structured logging, and a Docker setup.
- **Libraries:** FastAPI, Uvicorn, Pydantic, pytest, httpx; NumPy and wfdb only for the optional dataset script.
- **AI tools:** Claude (Anthropic) was used to help write the code, tests and documentation; I reviewed the code and can explain it.
