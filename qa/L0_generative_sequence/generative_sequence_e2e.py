#!/usr/bin/env python
# Copyright (c) 2023, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#  * Neither the name of NVIDIA CORPORATION nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
# OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys

sys.path.append("../common")

import unittest

import json
import requests
import sseclient
import numpy as np
import test_util as tu
import tritonclient.grpc as grpcclient
from tritonclient.utils import InferenceServerException

# GRPC streaming helpers..
import queue
from functools import partial
class UserData:
    def __init__(self):
        self._completed_requests = queue.Queue()

def callback(user_data, result, error):
    if error:
        user_data._completed_requests.put(error)
    else:
        user_data._completed_requests.put(result)


class GenerativeSequenceTest(tu.TestResultCollector):
    def test_generate_stream(self):
        headers = {"Accept": "text/event-stream"}
        url = "http://localhost:8000/v2/models/generative_sequence/generate_stream"
        inputs = {"INPUT": 2}
        res = requests.post(
            url,
            data=json.dumps(inputs),
            headers=headers
        )
        res.raise_for_status()
        client = sseclient.SSEClient(res)
        res_count = 2
        for event in client.events():
            res_count -= 1
            data = json.loads(event.data)
            self.assertIn("OUTPUT", data)
            self.assertEqual(res_count, data["OUTPUT"])
        self.assertEqual(0, res_count)
        
    def test_grpc_stream(self):
        user_data = UserData()
        with grpcclient.InferenceServerClient("localhost:8001") as triton_client:
            triton_client.start_stream(
                callback=partial(callback, user_data)
            )
            inputs = []
            inputs.append(grpcclient.InferInput("INPUT", [1,1], "INT32"))
            inputs[0].set_data_from_numpy(np.array([[2]], dtype=np.int32))
            
            triton_client.async_stream_infer(model_name="generative_sequence", inputs=inputs)
            res_count = 2
            while res_count > 0:
                data_item = user_data._completed_requests.get()
                res_count -= 1
                if type(data_item) == InferenceServerException:
                    raise data_item
                else:
                    self.assertEqual(res_count, data_item.as_numpy("OUTPUT")[0][0])
            self.assertEqual(0, res_count)

if __name__ == "__main__":
    unittest.main()