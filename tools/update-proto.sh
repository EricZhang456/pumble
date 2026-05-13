#!/bin/sh

set -e

BASE_DIR=$(dirname "$0")
PROTO_DIR="$BASE_DIR/../proto"
PROTO_SRC_DIR="$BASE_DIR/../src/pumble/_proto"

curl "https://raw.githubusercontent.com/mumble-voip/mumble/refs/heads/master/src/Mumble.proto" > "$PROTO_DIR/Mumble.proto"
curl "https://raw.githubusercontent.com/mumble-voip/mumble/refs/heads/master/src/MumbleUDP.proto" > "$PROTO_DIR/MumbleUDP.proto"

protoc --proto_path="$PROTO_DIR" --python_out="$PROTO_SRC_DIR" --pyi_out="$PROTO_SRC_DIR" "$PROTO_DIR/Mumble.proto"
protoc --proto_path="$PROTO_DIR" --python_out="$PROTO_SRC_DIR" --pyi_out="$PROTO_SRC_DIR" "$PROTO_DIR/MumbleUDP.proto"
