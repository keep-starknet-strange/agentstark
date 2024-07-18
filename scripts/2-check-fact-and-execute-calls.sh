#!/usr/bin/env bash

sncast --url "https://rpc.nethermind.io/sepolia-juno/?apikey=YOUR_API_KEY" \
  --account ag multicall run \
  --path multicall.toml
