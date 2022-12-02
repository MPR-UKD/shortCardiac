import pickle
import numpy as np
from xml.dom import minidom


def keepElementNodes(nodes):
    """Get the element nodes"""
    nodes2 = []
    for node in nodes:
        if node.nodeType == node.ELEMENT_NODE:
            nodes2 += [node]
    return nodes2


def parseContours(node):
    """
    Parse a Contours object. Each Contours object may contain several contours.
    We first parse the contour name, then parse the points and pixel size.
    """
    contours = {}
    for child in keepElementNodes(node.childNodes):
        contour_name = child.getAttribute("Hash:key")
        sup = 1
        for child2 in keepElementNodes(child.childNodes):
            if child2.getAttribute("Hash:key") == "Points":
                points = []
                for child3 in keepElementNodes(child2.childNodes):
                    x = float(
                        child3.getElementsByTagName("Point:x")[0].firstChild.data
                    )  # + 100
                    y = float(
                        child3.getElementsByTagName("Point:y")[0].firstChild.data
                    )  # + 100
                    points += [[x, y]]
            if child2.getAttribute("Hash:key") == "SubpixelResolution":
                sub = int(child2.firstChild.data)
        points = np.array(points)
        points /= sub
        contours[contour_name] = points
    return contours


def traverseNode(node, uid_contours):
    """Traverse the nodes"""
    child = node.firstChild
    while child:
        if child.nodeType == child.ELEMENT_NODE:
            # This is where the information for each dicom file starts
            if child.getAttribute("Hash:key") == "ImageStates":
                for child2 in keepElementNodes(child.childNodes):
                    # UID for the dicom file
                    uid = child2.getAttribute("Hash:key")
                    for child3 in keepElementNodes(child2.childNodes):
                        if child3.getAttribute("Hash:key") == "Contours":
                            contours = parseContours(child3)
                            if contours:
                                uid_contours[uid] = contours
        traverseNode(child, uid_contours)
        child = child.nextSibling


def parseFile(xml_name, coord_file):
    """Parse a cvi42 xml file"""
    dom = minidom.parse(xml_name)
    uid_contours = {}
    traverseNode(dom, uid_contours)

    data = {}
    for uid, contours in uid_contours.items():
        data[uid] = contours
    with open(coord_file, "wb") as f:
        pickle.dump(data, f)
