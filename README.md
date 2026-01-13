# MultAIchat
A tool for managing distributed AI with multiple personalities.

## Distributed architecture notes
- REST API
- WebRTC
  - Connect to STUN server and join a compute pool
  - Each client can tell other clients which processing type (models) it supports
  - Upon connecting, clients receive a list of peers and supported models that are currently in the pool
  - When new clients connect, other clients receive an updated list of pool members
  - Basic stats are collected per-peer (tokens / images per second, latency, etc)
  - When a request for a certain type of generation is made, the client can pick where to send the request from the list of available pool members
  - Challenges:
    - Routing queries to the right peer processor requires knowing their performance characteristics and balancing compute speed vs transfer speed / latency
    - Latency and computational availability changes with time and load
- Model adapters
  - Expose schema which specifies the types of models a given peer supports
    - model name
    - inputs
      - text
      - images
      - sounds
      - numeric parameters
    - outputs
      - image
      - text
      - audio
      - video
      - 3d


aide.model.define('sdxl-txt2img', {
  inputs: {
    prompt: aide.types.text,
    seed: int,
  },
  outputs: {
    image: aide.types.image
  }
})
aide.model.define('sdxl-img2img', {
  inputs: {
    prompt: aide.types.text,
    img: aide.types.image,
    seed: int,
  },
  outputs: {
    image: aide.types.image
  }
})
aide.model.define('llama3-chat-8b', {
  inputs: {
    prompt: aide.types.text,
    temperature: float,
    top_p: float,
  }
  outputs: {
    prompt: aide.types.text
  }
})
