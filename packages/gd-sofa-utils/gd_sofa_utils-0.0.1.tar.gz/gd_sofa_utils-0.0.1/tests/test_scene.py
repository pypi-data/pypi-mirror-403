import logging
from pathlib import Path
import unittest

import gdutils as gd
from gdsofa import *
from gdsofa.core.node import Node, BBOX  # extra imports for direct Node / BBOX tests


class TestGdsofaScene(unittest.TestCase):
    def setUp(self) -> None:
        self.root = RootNode()
        self.root + DefaultAnimationLoop()

    def test_root(self):
        self.assertEqual(self.root.name, "root")

        cond = lambda x: "AnimationLoop" in x.class_name
        self.assertEqual(
            self.root.find(callback=cond).class_name, "DefaultAnimationLoop"
        )

    def test_link(self):
        meca_obj = Object("FakeObject", name="my-obj")

        r = self.root = RootNode()
        obj1 = r + meca_obj
        x = r.add_child("child")
        obj2 = x + meca_obj(name="my-child-obj", foo=Link(obj1))
        obj3 = x + Object("A", foo=MultiLink(obj1, (obj2, "some_data")))

        r.print()
        self.assertEqual(obj3.kw.foo, ["@../my-obj", "@my-child-obj.some_data"])
        self.assertEqual((l := Link(obj2)).resolve(r), "@child/my-child-obj")
        self.assertEqual(l.resolve(x), "@my-child-obj")


class TestNodeAndComponents(unittest.TestCase):
    def test_node_hierarchy_and_paths(self):
        root = Node("root")
        child = root.add_child("child")
        grand = child.add_child("grand")

        # parents
        self.assertIs(child.parent, root)
        self.assertIs(grand.parent, child)

        # get_root
        self.assertIs(grand.get_root(), root)
        self.assertIs(root.get_root(), root)

        # paths
        self.assertEqual(str(root.path), "@")
        self.assertEqual(str(child.path), "@child")
        self.assertEqual(str(grand.path), "@child/grand")

        # get_node recursion
        self.assertIs(root.get_node("child"), child)
        self.assertIs(root.get_node("grand"), grand)
        self.assertIsNone(root.get_node("does_not_exist"))

    def test_path_from(self):
        root = Node("root")
        a = root.add_child("a")
        b = a.add_child("b")

        # same node
        self.assertEqual(str(a.path_from(a)), "@")

        # descendant from ancestor
        self.assertEqual(str(b.path_from(a)), "@b")

        # ancestor from descendant
        self.assertEqual(str(a.path_from(b)), "@..")

        # between siblings
        c = root.add_child("c")
        self.assertEqual(str(c.path_from(a)), "@../c")
        self.assertEqual(str(a.path_from(c)), "@../a")

    def test_nodes_up2down_and_object_generators(self):
        root = Node("root")
        n1 = root.add_child("n1")
        n2 = n1.add_child("n2")
        n3 = root.add_child("n3")

        o_root = Object("C", name="root_obj")
        o_n1 = Object("C", name="n1_obj")
        o_n2 = Object("C", name="n2_obj")
        o_n3 = Object("C", name="n3_obj")

        root + o_root
        n1 + o_n1
        n2 + o_n2
        n3 + o_n3

        # nodes_up2down order
        self.assertEqual(
            [n.name for n in root.nodes_up2down], ["root", "n1", "n2", "n3"]
        )

        # up2down over objects
        self.assertEqual(
            [o.name for o in root.up2down],
            ["root_obj", "n1_obj", "n2_obj", "n3_obj"],
        )

        # down2up from deepest node
        self.assertEqual([o.name for o in n2.down2up], ["n2_obj", "n1_obj", "root_obj"])

        # last property
        self.assertIs(n2.last, o_n2)

    def test_find_and_rfind(self):
        root = Node("root")
        n1 = root.add_child("n1")
        n2 = n1.add_child("n2")

        o_root = Object("Comp", name="at_root")
        o_n1 = Object("Comp", name="at_n1")
        o_n2 = Object("Comp", name="at_n2")

        root + o_root
        n1 + o_n1
        n2 + o_n2

        # find from root (downwards)
        self.assertIs(root.find(name="at_root"), o_root)
        self.assertIs(root.find(name="at_n1"), o_n1)
        self.assertIs(root.find(name="at_n2"), o_n2)

        # find with callback
        cond = lambda x: hasattr(x, "name") and x.name == "at_n2"
        self.assertIs(root.find(callback=cond), o_n2)

        # rfind (upwards)
        self.assertIs(n2.rfind(name="at_root"), o_root)
        self.assertIs(n1.rfind(name="at_root"), o_root)

        # rfind that fails
        log.info("Error incoming :")
        with self.assertRaises(KeyError):
            n1.rfind(name="at_n2")
        log.info("End error.")

        # rfind silent
        self.assertIsNone(n1.rfind(name="does_not_exist", silent=True))

    def test_set_bbox_and_bbox_value(self):
        n = Node("root")

        # xmin_ymin format
        n.set_bbox([0, 1, 2, 3, 4, 5], fmt="xmin_ymin")
        self.assertIsInstance(n.bbox, BBOX)
        self.assertEqual(n.bbox.min, [0.0, 1.0, 2.0])
        self.assertEqual(n.bbox.max, [3.0, 4.0, 5.0])
        self.assertEqual(n.bbox.value, "0.0 1.0 2.0 3.0 4.0 5.0")

        # xmin_xmax format
        n2 = Node("root2")
        n2.set_bbox([0, 3, 1, 4, 2, 5], fmt="xmin_xmax")
        self.assertEqual(n2.bbox.min, [0.0, 1.0, 2.0])
        self.assertEqual(n2.bbox.max, [3.0, 4.0, 5.0])
        self.assertEqual(n2.bbox.value, "0.0 1.0 2.0 3.0 4.0 5.0")

        # direct BBOX
        b = BBOX(min=[0, 0, 0], max=[1, 2, 3])
        self.assertEqual(b.value, "0.0 0.0 0.0 1.0 2.0 3.0")

    def test_object_path_and_attach(self):
        root = Node("root")
        child = root.add_child("child")

        o_root = Object("Comp", name="root_obj")
        o_child = Object("Comp", name="child_obj")

        root + o_root
        child + o_child

        # path for attached objects
        self.assertEqual(str(o_root.path), "@root_obj")
        self.assertEqual(str(o_child.path), "@child/child_obj")

        # path for unattached object should fail
        o = Object("Comp2")
        with self.assertRaises(RuntimeError):
            _ = o.path  # noqa: F841

    def test_object_clone_with_call(self):
        templ = Object("MyComponent", name="templ", foo=1)
        clone = templ(bar=2)

        self.assertIsNot(templ, clone)
        self.assertEqual(templ.class_name, clone.class_name)

        # original unchanged
        self.assertEqual(templ.kw.foo, 1)
        self.assertNotIn("bar", templ.kw)

        # clone has merged kw
        self.assertEqual(clone.kw.foo, 1)
        self.assertEqual(clone.kw.bar, 2)

        # current implementation keeps the same name
        self.assertEqual(clone.name, templ.name)

    def test_node_add_with_nodes_and_objects(self):
        root = Node("root")
        child = Node("child")

        # add a child node using add()
        root.add(child)
        self.assertIs(child.parent, root)
        self.assertIn(child, root.children)

        # add a component
        o1 = Object("Comp", name="c1")
        root.add(o1)
        self.assertIs(o1.parent, root)
        self.assertIn(o1, root.objs)

        # add several components at once
        o2 = Object("Comp", name="c2")
        o3 = Object("Comp", name="c3")
        root.add([o2, o3])
        self.assertIn(o2, root.objs)
        self.assertIn(o3, root.objs)

        # __add__ forwards to add
        o4 = Object("Comp", name="c4")
        root + o4
        self.assertIn(o4, root.objs)

    def test_update_links_and_multilinks(self):
        root = Node("root")
        base = Object("Base", name="base_obj")
        root + base

        child = root.add_child("child")

        o = Object(
            "WithLinks",
            name="with_links",
            single=Link(base),
            multi=MultiLink(base),
            untouched=42,
        )
        child + o

        # before update_links, kw entries are Link / MultiLink instances
        self.assertIsInstance(o.kw.single, Link)
        self.assertIsInstance(o.kw.multi, MultiLink)
        self.assertEqual(o.kw.untouched, 42)

        # update links from the root
        root.update_links()

        # after update_links, they are resolved strings / list of strings
        self.assertIsInstance(o.kw.single, str)
        self.assertEqual(o.kw.single, "@../base_obj")
        self.assertEqual(o.kw.multi, ["@../base_obj"])

        # non-link data unchanged
        self.assertEqual(o.kw.untouched, 42)


log = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    log = gd.get_logger()

    unittest.main()
