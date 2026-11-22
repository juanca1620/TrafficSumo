FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY pytest.ini .
COPY controller/ ./controller/
COPY analysis/ ./analysis/
COPY tools/ ./tools/
COPY network/ ./network/
COPY demand/ ./demand/
COPY scenarios/ ./scenarios/
COPY tests/ ./tests/
COPY run_tests.py .
COPY run_pipeline.py .
CMD ["python", "-c", "from controller.adaptive_controller import decidir_accion, validar_parametros; from analysis.run_comparison import calcular_mejora; from tools.validar_config import validar_red, validar_demanda; assert validar_red('network/intersection.net.xml')[0] and validar_demanda('demand/routes.rou.xml')[0] and round(calcular_mejora(100.0, 49.2), 1) == 50.8; print('SGT listo:', decidir_accion(15, 0, True), validar_parametros(10, 45, 3))"]
