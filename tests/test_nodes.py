import types
import unittest

from _pack import comfy_available, load_full_pack

HAVE_COMFY = comfy_available()
LEGACY_IDS = ("MiniMaxH3DirectorCS", "MiniMaxH3PreviewOverrideCS", "MiniMaxH3RetakeStitchCS", "MiniMaxH3EnhancePromptCS", "MiniMaxH3SaveLastFrameCS")
HFD_IDS = ("HFDContextImage", "HFDContextVideo", "HFDContextAudio", "HFDContextText", "HFDDirector", "HFDChunkConditioning", "HFDCollect")


@unittest.skipUnless(HAVE_COMFY, "ComfyUI is not importable")
class Registration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = load_full_pack()

    def test_ng_nodes_are_registered_next_to_the_legacy_ones(self):
        mappings = self.pack.NODE_CLASS_MAPPINGS
        for node_id in LEGACY_IDS + HFD_IDS:
            self.assertIn(node_id, mappings)
        self.assertTrue(all(not n.endswith("CS") for n in HFD_IDS))

    def test_the_old_director_is_marked_legacy_without_changing_its_id(self):
        schema = self.pack.NODE_CLASS_MAPPINGS["MiniMaxH3DirectorCS"].GET_SCHEMA()
        self.assertEqual(schema.display_name, "MiniMax H3 Director (Legacy)")
        self.assertEqual(schema.category, "MiniMax H3/Legacy")
        self.assertTrue(schema.description.startswith("LEGACY"))
        self.assertEqual(self.pack.NODE_DISPLAY_NAME_MAPPINGS["MiniMaxH3DirectorCS"], "MiniMax H3 Director (Legacy)")

    def test_display_names_exist(self):
        expected = {"HFDContext" + kind: "H3 Context " + kind for kind in ("Image", "Video", "Audio")}
        expected["HFDContextText"] = "H3 Context Text (Style & Rules)"   # the story belongs in the Director's Prompt (2026-10-18)
        expected.update(HFDDirector="HFD Chunk Planner", HFDChunkConditioning="HFD Chunk Conditioning", HFDCollect="HFD Collect")
        for node_id, name in expected.items():
            self.assertEqual(self.pack.NODE_DISPLAY_NAME_MAPPINGS[node_id], name, node_id)

    def test_node_list_shows_what_users_build_with(self):
        # User 2026-10-18: too many test nodes, the list did not fit. Internal nodes stay registered (Render Sequence expands
        # into them, saved workflows load them) but ComfyUI does not list them; the blocks of an own loop have their group.
        internal = ("HFDChunkConditioning", "HFDChunkNoise", "HFDChunkSampling", "HFDResumeChunk", "HFDControlChunk", "HFDProjectChunks",
                    "HFDTurboLora", "HFDAIRequest", "HFDAICheckEncoder", "HFDAIReadMedia", "HFDAIResult")
        loop = ("HFDCollect", "HFDCollectVideo", "HFDControlVideo", "HFDDirector", "HFDDirectorStudio", "HFDRenderSequence", "MiniMaxH3PreviewOverrideCS")
        for node_id in internal:
            schema = self.pack.NODE_CLASS_MAPPINGS[node_id].GET_SCHEMA()
            self.assertEqual((schema.category, schema.is_dev_only), ("MiniMax H3/NG/Technical", True), node_id)
        for node_id in loop:
            schema = self.pack.NODE_CLASS_MAPPINGS[node_id].GET_SCHEMA()
            self.assertEqual((schema.category, schema.is_dev_only), ("MiniMax H3/NG/Custom loop", False), node_id)
        for node_id in ("MiniMaxH3DirectorCS", "MiniMaxH3EnhancePromptCS", "MiniMaxH3RetakeStitchCS", "MiniMaxH3SaveLastFrameCS"):
            self.assertEqual(self.pack.NODE_CLASS_MAPPINGS[node_id].GET_SCHEMA().category, "MiniMax H3/Legacy", node_id)

    def test_schemas_have_unique_input_ids_and_a_category(self):
        for node_id in HFD_IDS:
            schema = self.pack.NODE_CLASS_MAPPINGS[node_id].GET_SCHEMA()
            ids = [i.id for i in schema.inputs]
            self.assertEqual(len(ids), len(set(ids)), node_id)
            category = {"HFDChunkConditioning": "MiniMax H3/NG/Technical", "HFDDirector": "MiniMax H3/NG/Custom loop",
                        "HFDCollect": "MiniMax H3/NG/Custom loop"}.get(node_id, "HyperFlow Director")
            self.assertEqual(schema.category, category)

    def test_loop_nodes_take_and_give_what_the_loop_needs(self):
        director = self.pack.NODE_CLASS_MAPPINGS["HFDDirector"].GET_SCHEMA()
        self.assertTrue(director.outputs[0].is_output_list)
        chunk = self.pack.NODE_CLASS_MAPPINGS["HFDChunkConditioning"].GET_SCHEMA()
        self.assertEqual([o.display_name for o in chunk.outputs], ["model", "positive", "latent", "prompt"])
        self.assertTrue(self.pack.NODE_CLASS_MAPPINGS["HFDCollect"].GET_SCHEMA().is_input_list)

    def test_the_ai_loader_seed_has_no_randomize_switch(self):
        """ComfyUI hangs a "control after generate" switch on any widget named "seed" unless the
        schema says otherwise, and the check is a nullish fallback - only an explicit False wins.

        The AI Loader must not have one. Its panel already offers "Fixed seed" beside the field, and
        that switch is the honest control: the seed here belongs to the AI request, not to the
        render queue, so "randomize" on the node and "Fixed seed" in the panel were two controls for
        one decision, and following one silently contradicted the other."""
        seed = self._input("HFDAIProvider", "seed")
        self.assertIs(seed.control_after_generate, False,
                      "an omitted or None value makes the frontend add the switch back")

    def test_the_render_nodes_keep_their_randomize_switch(self):
        """The opposite end of the same rule: on a render node the queue does own the seed, so the
        switch belongs there. Suppressing it everywhere would take away a control that is correct."""
        self.assertIs(self._input("HFDRenderSequence", "seed").control_after_generate, True)

    def _input(self, node_id, input_id):
        schema = self.pack.NODE_CLASS_MAPPINGS[node_id].GET_SCHEMA()
        found = [i for i in schema.inputs if i.id == input_id]
        self.assertEqual(len(found), 1, "%s has no input %s" % (node_id, input_id))
        return found[0]


@unittest.skipUnless(HAVE_COMFY, "ComfyUI is not importable")
class Execution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = load_full_pack()
        cls.nodes = cls.pack.NODE_CLASS_MAPPINGS
        cls.context_nodes = __import__("sys").modules["hfd_full_pack.hfd.nodes.context_nodes"]

    def out(self, node_id, **kw):
        return self.nodes[node_id].execute(**kw).args

    def test_image_context(self):
        (item,) = self.out("HFDContextImage", image="refs/alice.png [input]", name="Alice", description="a woman ", content="character",
                           usage="reference", preserve="high")
        self.assertEqual((item.id, item.source, item.media, item.description), ("image_alice", "refs/alice.png", "image", "a woman"))

    def test_name_falls_back_to_the_file(self):
        (item,) = self.out("HFDContextImage", image="refs/old castle.png", name="", description="", content="location", usage="reference", preserve="low")
        self.assertEqual((item.name, item.id), ("old castle", "image_old_castle"))

    def test_audio_context_reads_its_length_and_speaker(self):
        saved = self.context_nodes.probe.duration_seconds
        self.context_nodes.probe.duration_seconds = lambda source: 7.5
        try:
            (item,) = self.out("HFDContextAudio", audio="v.wav", name="V", description="", content="voice", usage="voice", preserve="high", speaker=" Alice ")
        finally:
            self.context_nodes.probe.duration_seconds = saved
        self.assertEqual((item.length_s, item.speaker, item.usage), (7.5, "Alice", ("voice",)))

    def test_replacing_a_file_changes_the_cache_key_of_its_context_node(self):
        import os
        import folder_paths
        path = os.path.join(folder_paths.get_input_directory(), "ng_stamp_test.png")
        try:
            with open(path, "wb") as f:
                f.write(b"first")
            node = self.nodes["HFDContextImage"]
            before = node.fingerprint_inputs(image="ng_stamp_test.png")
            self.assertEqual(before, node.fingerprint_inputs(image="ng_stamp_test.png [input]"))
            with open(path, "wb") as f:
                f.write(b"second version")
            self.assertNotEqual(before, node.fingerprint_inputs(image="ng_stamp_test.png"))
        finally:
            if os.path.exists(path):
                os.remove(path)
        self.assertEqual(self.nodes["HFDContextAudio"].fingerprint_inputs(audio="not there.wav"), "missing")

    def test_text_context_keeps_the_text(self):
        (item,) = self.out("HFDContextText", text="Keep the camera slow.", name="", description="", content="rules", usage="style", preserve="high")
        self.assertEqual((item.media, item.source), ("text", "Keep the camera slow."))

    def test_director_plans_a_sixty_second_project(self):
        (alice,) = self.out("HFDContextImage", image="alice.png", name="Alice", description="a woman", content="character", usage="reference", preserve="high")
        chunks, warnings, plan = self.out("HFDDirector", idea="Alice walks through a station.", shots="", project_seconds=60.0, chunk_seconds=10.0,
                                          width=768, height=1152, mode="auto", continuity="video_audio", pin_frames="22", soundscape="", music="",
                                          contexts={"context_1": alice})
        self.assertGreaterEqual(len(chunks), 6)
        self.assertTrue(all(j.compiled.mode == "ref2va" for j in chunks))
        self.assertIn("chunk 1:", plan)
        self.assertIn("joins", warnings)

    def test_director_without_contexts(self):
        chunks, warnings, plan = self.out("HFDDirector", idea="A dog runs.", shots="", project_seconds=8.0, chunk_seconds=0.0, width=768, height=1152,
                                          mode="auto", continuity="none", pin_frames="22", soundscape="", music="")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].compiled.mode, "t2va")

    def test_lazy_model_choice_follows_the_chunks_mode(self):
        node = self.nodes["HFDChunkConditioning"]
        unc = __import__("sys").modules["hfd_full_pack.hfd.nodes.chunk_node"].UNCONNECTED
        ref = types.SimpleNamespace(compiled=types.SimpleNamespace(mode="ref2va"))
        fl = types.SimpleNamespace(compiled=types.SimpleNamespace(mode="t2va"))
        self.assertEqual(node.check_lazy_status(chunk=ref, model_fl2va=None, model_ref2va=None), ["model_ref2va"])
        self.assertEqual(node.check_lazy_status(chunk=fl, model_fl2va=None, model_ref2va=None), ["model_fl2va"])
        self.assertEqual(node.check_lazy_status(chunk=ref, model_fl2va=None, model_ref2va=unc), ["model_fl2va"])
        self.assertEqual(node.check_lazy_status(chunk=ref, model_fl2va=object(), model_ref2va=unc), [])
        self.assertEqual(node.check_lazy_status(chunk=ref, model_fl2va=unc, model_ref2va=unc), [])


if __name__ == "__main__":
    unittest.main()
