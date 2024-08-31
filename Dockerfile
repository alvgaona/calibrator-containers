FROM ghcr.io/prefix-dev/pixi:0.28.2 AS build

# copy source code, pixi.toml and pixi.lock to the container
COPY . /app
WORKDIR /app

RUN pixi install

# Create the shell-hook bash script to activate the environment
RUN pixi shell-hook > /shell-hook.sh

# extend the shell-hook script to run the command passed to the container
RUN echo 'exec "$@"' >> /shell-hook.sh

FROM ubuntu:22.04 AS production

COPY --from=build /app/.pixi/envs/default /app/.pixi/envs/default
COPY --from=build /app/lambda_function.py /app/lambda_function.py
COPY --from=build /app/entrypoint.sh /entrypoint.sh
COPY --from=build /shell-hook.sh /shell-hook.sh

ENTRYPOINT ["/entrypoint.sh"]
