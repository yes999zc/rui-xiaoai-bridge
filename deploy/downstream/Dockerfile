# syntax=docker/dockerfile:1
#
# Phase 1 PREVIEW image: official rui 0.6.0 + this out-of-tree LX06 plug.
#
# The 0.6.0 image still ships the in-tree reference plug (`xiaoai-lx06` under
# /opt/rui-plugins/xiaoai). Same plugin id => the first catalog scan wins, and an
# operator cannot replace a builtin adapter name. So this preview deliberately puts
# our plug in a *separate, higher-priority* RUI_PLUGINS_DIR root: roots from the env
# are scanned before the built-in image directory, which makes the winner explicit
# instead of relying on directory sort order.
#
# Phase 2 removes the in-tree plug upstream; this extra root then goes away and the
# plug ships under /opt/rui-plugins like any other image plug.
#
#   docker build -f deploy/downstream/Dockerfile -t rui-xiaoai:0.1.0 .
ARG RUI_IMAGE=ghcr.io/yes999zc/rui:0.6.0@sha256:abef1f276c3c21e9155d97c98913ee6c2e98fdfe842e43b90f64a5db6c12b241
FROM ${RUI_IMAGE}

# Manifest + package live together (plugin.yaml is inside the package directory), so
# the catalog scan, the co-located manifest lookup and README's RUI_PLUGINS_DIR recipe
# all agree on one layout.
COPY --chown=1000:1000 src/rui_xiaoai_bridge /opt/rui-xiaoai-plugins/rui_xiaoai_bridge

# Ours first; keep the in-tree plug importable for the 0.6.x overlap window.
ENV PYTHONPATH=/opt/rui-xiaoai-plugins:/opt/rui-plugins/xiaoai \
    RUI_PLUGINS_DIR=/opt/rui-xiaoai-plugins
