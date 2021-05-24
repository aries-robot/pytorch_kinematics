import math

import tensorflow as tf

from tensorflow_kinematics import frame
from tensorflow_kinematics import transforms
from tensorflow_kinematics.transforms import Transform3d
from urdf_parser_py.urdf import Mesh, Cylinder, Box, Sphere

JOINT_TYPE_MAP = {'revolute':  'revolute',
                  'prismatic': 'prismatic',
                  'fixed':     'fixed'}


def _convert_transform(pose):
    if pose is None:
        return Transform3d()
    else:
        return Transform3d(rot=transforms.euler_angles_to_matrix(tf.constant(pose[3:]), "ZYX"), pos=pose[:3])


def _convert_visuals(visuals):
    vlist = []
    for v in visuals:
        v_tf = _convert_transform(v.pose)
        if isinstance(v.geometry, Mesh):
            g_type = "mesh"
            g_param = v.geometry.filename
        elif isinstance(v.geometry, Cylinder):
            g_type = "cylinder"
            v_tf = v_tf.compose(
                Transform3d(rot=transforms.euler_angles_to_matrix(tf.constant([0.5 * math.pi, 0, 0]), "ZYX")))
            g_param = (v.geometry.radius, v.geometry.length)
        elif isinstance(v.geometry, Box):
            g_type = "box"
            g_param = v.geometry.size
        elif isinstance(v.geometry, Sphere):
            g_type = "sphere"
            g_param = v.geometry.radius
        else:
            g_type = None
            g_param = None
        vlist.append(frame.Visual(v_tf, g_type, g_param))
    return vlist


def _build_chain_recurse(root_frame, lmap, joints):
    children = []
    for j in joints:
        if j.parent == root_frame.link.name:
            child_frame = frame.Frame(j.child + "_frame")
            link_p = lmap[j.parent]
            link_c = lmap[j.child]
            t_p = _convert_transform(link_p.pose)
            t_c = _convert_transform(link_c.pose)
            child_frame.joint = frame.Joint(j.name, offset=t_p.inverse().compose(t_c),
                                            joint_type=JOINT_TYPE_MAP[j.type], axis=j.axis.xyz)
            child_frame.link = frame.Link(link_c.name, offset=Transform3d(),
                                          visuals=_convert_visuals(link_c.visuals))
            child_frame.children = _build_chain_recurse(child_frame, lmap, joints)
            children.append(child_frame)
    return children