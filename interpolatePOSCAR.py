#!/usr/bin/env python

import os
import sys
import re


def getImageNum(initDirs):
    max_num = 0
    p = re.compile(r'\d\d')
    for dir in initDirs:
        m = p.match(dir)
        if m:
            num = int(m.group(0))
            if num > max_num:
                max_num = num

    if max_num == 0:
        print("Error: you should prepare directories for NEB: 00 01 02 ...")
        sys.exit()

    return max_num + 1


def makeDirs(num):
    dirs = []
    for i in range(num):
        dirname = "{:02}".format(i)
        dirs.append(dirname)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

    return dirs


class Poscar:

    def __init__(self):
        self.comment = ""
        self.scale = 0
        self.a = []
        self.b = []
        self.c = []
        self.elements = []
        self.numOfElements = []
        self.type = ""
        self.atoms = []

    def readPoscar(self, filename):
        with open(filename) as f:
            lines = [s.strip() for s in f.readlines()]

        self.comment = lines[0]
        self.scale = float(lines[1])
        self.a = [float(f) for f in lines[2].split()]
        self.b = [float(f) for f in lines[3].split()]
        self.c = [float(f) for f in lines[4].split()]
        self.elements = lines[5].split()
        self.numOfElements = [int(f) for f in lines[6].split()]
        self.type = lines[7]

        for i in range(sum(self.numOfElements)):
            self.atoms.append([float(f) for f in lines[i+8].split()])


    def difference(self, poscarFirst):
        diff = Poscar()

        diff.comment = self.comment
        diff.scale = self.scale - poscarFirst.scale
        diff.a = [x - y for (x, y) in zip(self.a, poscarFirst.a)]
        diff.b = [x - y for (x, y) in zip(self.b, poscarFirst.b)]
        diff.c = [x - y for (x, y) in zip(self.c, poscarFirst.c)]
        diff.elements = self.elements
        diff.numOfElements = self.numOfElements

        for (atomL, atomF) in zip(self.atoms, poscarFirst.atoms):
            vec = [x - y for (x, y) in zip(atomL, atomF)]
            for key, val in enumerate(vec):
                if val > 0.5:
                    vec[key] -= 1
                elif val < -0.5:
                    vec[key] += 1

            diff.atoms.append(vec)

        return diff


if __name__ == '__main__':

    # get dirs
    initDirs = [f for f in os.listdir(".") if os.path.isdir(os.path.join(".", f))]

    # get Number of image
    imageNum = getImageNum(initDirs)

    # make dirs
    dirs = makeDirs(imageNum)

    # read POSCARs
    poscarFirst = Poscar()
    poscarFirst.readPoscar("00/POSCAR")
    poscarLast = Poscar()
    poscarLast.readPoscar(dirs[-1] + "/POSCAR")
    deltaPoscar = poscarLast.difference(poscarFirst)

    # make POSCAR for Images
    delta = 1
    for dir in dirs[1:-1]:
        lines = []
        lines.append(poscarFirst.comment)
        lines.append(" {:20.16f}".format(poscarFirst.scale + deltaPoscar.scale * delta / imageNum))
        lines.append("   {0[0]:20.16f} {0[1]:20.16f} {0[2]:20.16f}".format(
            [x + y * delta / imageNum for (x, y) in zip(poscarFirst.a, deltaPoscar.a)]))
        lines.append("   {0[0]:20.16f} {0[1]:20.16f} {0[2]:20.16f}".format(
            [x + y * delta / imageNum for (x, y) in zip(poscarFirst.b, deltaPoscar.b)]))
        lines.append("   {0[0]:20.16f} {0[1]:20.16f} {0[2]:20.16f}".format(
            [x + y * delta / imageNum for (x, y) in zip(poscarFirst.c, deltaPoscar.c)]))
        lines.append("   {}".format("  ".join(poscarFirst.elements)))
        lines.append("   {}".format("  ".join([str(f) for f in poscarFirst.numOfElements])))
        lines.append(poscarFirst.type)
        for atomF, atomDelta in zip(poscarFirst.atoms, deltaPoscar.atoms):
            lines.append("  {0[0]:20.16f} {0[1]:20.16f} {0[2]:20.16f}".format(
                [x + y * delta / imageNum for (x, y) in zip(atomF, atomDelta)]))

        with open(dir + "/POSCAR", "w") as f:
            f.write("\n".join(lines))

        delta += 1
