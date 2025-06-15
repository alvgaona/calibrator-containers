FROM ghcr.io/prefix-dev/pixi:0.48.1 AS build

ARG FUNCTION_DIR
ARG PIXI_ENV

WORKDIR /app

# Force pixi to create its data inside /app so we can copy it later
ENV PIXI_HOME=/app/.pixi

COPY pixi.toml /app
COPY pixi.lock /app
COPY ./${FUNCTION_DIR}/lambda_function.py /app
COPY entrypoint.sh /app

RUN pixi install -e ${PIXI_ENV}

# Create the shell-hook bash script to activate the environment
RUN pixi shell-hook -e ${PIXI_ENV} > /shell-hook.sh

# extend the shell-hook script to run the command passed to the container
RUN echo 'exec "$@"' >> /shell-hook.sh

FROM ubuntu:22.04 AS production

ARG PIXI_ENV

COPY --from=build /app/.pixi/envs/${PIXI_ENV} /app/.pixi/envs/${PIXI_ENV}
COPY --from=build /app/lambda_function.py /app/lambda_function.py
COPY --from=build /app/entrypoint.sh /entrypoint.sh
COPY --from=build /shell-hook.sh /shell-hook.sh

WORKDIR /app

ENTRYPOINT ["/entrypoint.sh"]
