#!/bin/sh
# Install the plug manifest where rui's *catalog* (wizard, GET /api/v1/plugs,
# resolve_device_plug) looks for user plugs: <data_dir>/plugs/xiaoai-lx06/.
#
# Why this is not always enough on rui 0.6.x:
#   The official 0.6.0 image still ships the in-tree plug with the same plugin id.
#   Builtin entries win on a shared id, so in that image this user copy is shadowed
#   and the wizard reports a duplicate. It becomes the effective install after
#   Phase 2 removes the in-tree plug, or on a host whose image does not ship it.
#   The adapter itself still has to be named in RUI_ADAPTER_PLUGINS (see README);
#   rui never executes a user plug just because it is in the data directory.
#
# Usage (from the repo dir):
#   sh deploy/install-plug-manifest.sh ~/rui/data
set -eu

data_dir="${1:?usage: install-plug-manifest.sh <data_dir>  (e.g. ~/rui/data)}"
src_dir="$(CDPATH= cd -- "$(dirname -- "$0")/../src/rui_xiaoai_bridge" && pwd)"
plug_id="xiaoai-lx06"
dst="$data_dir/plugs/$plug_id"

test -f "$src_dir/plugin.yaml" || { echo "missing $src_dir/plugin.yaml" >&2; exit 1; }
test -d "$src_dir/devices" || { echo "missing $src_dir/devices/" >&2; exit 1; }

mkdir -p "$dst/devices"
install -m 0644 "$src_dir/plugin.yaml" "$dst/plugin.yaml"
for f in "$src_dir"/devices/*.yaml; do
  install -m 0644 "$f" "$dst/devices/"
done
echo "installed manifest -> $dst"
echo "adapter registration: RUI_ADAPTER_PLUGINS=lx06=rui_xiaoai_bridge.adapter:build"
echo "package path:         PYTHONPATH=<repo>/src"
