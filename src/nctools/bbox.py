# vim:fileencoding=utf-8
# Copyright © 2013-2015 R.F. Smith <rsmith@xs4all.nl>. All rights reserved.
# $Date: 2015-04-27 18:04:10 +0200 $
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.

"""Operations on two or three dimensional bounding boxes."""


class BBox(object):
    __slots__ = ['minx', 'maxx', 'miny', 'maxy', 'minz', 'maxz', 'dim']

    def __init__(self, pnts):
        """Create a BBox from a list of points.

        :param pnts: a list of 2-tuples or 3-tuples of numbers
        """
        if not pnts:
            raise ValueError('no points to create BBox')
        if len(pnts) in (2, 3) and isinstance(pnts[0], (int, float)):
            pnts = [pnts]
        if len(pnts[0]) == 2:
            self.dim = 2
            x, y = zip(*pnts)
            self.minx, self.maxx = min(x), max(x)
            self.miny, self.maxy = min(y), max(y)
            self.minz, self.maxz = None, None
        elif len(pnts[0]) == 3:
            self.dim = 3
            x, y, z = zip(*pnts)
            self.minx, self.maxx = min(x), max(x)
            self.miny, self.maxy = min(y), max(y)
            self.minz, self.maxz = min(z), max(z)
        else:
            raise ValueError('pnts must contain 2-tuples or 3-tuples')

    def __str__(self):
        s2 = '<BBox {} ≤ x ≤ {}, {} ≤ y ≤ {} >'
        s3 = '<BBox {} ≤ x ≤ {}, {} ≤ y ≤ {}, {} ≤ z ≤ {} >'
        if self.dim == 2:
            return s2.format(self.minx, self.maxx, self.miny, self.maxy)
        s3.format(self.minx, self.maxx, self.miny, self.maxy,
                  self.minz, self.maxz)

    def update(self, pnts):
        """Grow the BBox to include pnts.

        :param pnts: a list of 2-tuples or 3-tuples of numbers
        """
        if len(pnts) in (2, 3) and isinstance(pnts[0], (int, float)):
            pnts = [pnts]
        tp = pnts[:]
        if self.dim != len(pnts[0]):
            raise ValueError('dimension of pnts[0] not conform bbox.')
        if self.dim == 2:
            tp += [(self.minx, self.miny),
                   (self.maxx, self.maxy)]
            self.__init__(tp)
        else:  # dim == 3
            tp += [(self.minx, self.miny, self.minz),
                   (self.maxx, self.maxy, self.maxz)]
            self.__init__(tp)

    def inside(self, pnts):
        """Determine if all the points are inside the BBox.

        :param pnts: a list of 2-tuples or 3-tuples of numbers
        :returns: True if all points are in the BBox.
        """
        single = False
        if len(pnts) in (2, 3) and isinstance(pnts[0], (int, float)):
            pnts = [pnts]
            single = True
        if len(pnts[0]) != self.dim:
            raise ValueError('dimension of pnts[0] not conform bbox.')
        if self.dim == 2:
            rv = [(self.minx <= p[0] <= self.maxx and
                   self.miny <= p[1] <= self.maxy) for p in pnts]
        else:
            rv = [(self.minx <= p[0] <= self.maxx and
                   self.miny <= p[1] <= self.maxy and
                   self.minz <= p[2] <= self.maxz) for p in pnts]
        if single:
            return rv[0]
        return rv

    @property
    def width(self):
        """Returns the width of the bounding box
        :returns: width of the bounding box
        """
        return self.maxx - self.minx

    @property
    def height(self):
        """Returns the height of the bounding box
        :returns: height of the bounding box
        """
        return self.maxy - self.miny

    @property
    def points(self):
        if self.dim == 2:
            return (self.minx, self.miny), (self.maxx, self.maxy)
        return ((self.minx, self.miny, self.minz),
                (self.maxx, self.maxy, self.maxz))


def merge(bbs):
    """Merge a list of bounding boxes

    :bbs: A tuple or list of bounding boxes.
    :returns: A new BBox then encompasses them all.
    """
    pnts = [p for b in bbs for p in b.points]
    return BBox(pnts)
