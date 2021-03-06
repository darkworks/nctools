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

"""Module for reading and writing DXF files. Only a subset of entities is
supported; LINE, ARC and POLYLINE."""

import datetime
import math
from nctools import ent


def reader(name):
    """Read a DXF file.

    :param name: The name of the file to read.
    :returns: A list of entities.
    """
    with open(name, 'r') as f:
        data = [s.strip() for s in f.readlines()]
    soe = data.index('ENTITIES')+1
    eoe = data.index('ENDSEC', soe)
    lines = data[soe:eoe]
    entities = _get_lines(lines)
    entities += _get_arcs(lines)
    entities += _get_circles(lines)
    entities += _get_polylines(lines)
    entities.sort(key=lambda x: x.index)
    return entities


def writer(name, progname, entities):
    """Write a DXF file.

    :param name: The name of the file to write.
    :entities: entities to write to the file
    """
    a = 'This conversion was started on {}'
    b = 'This file contains {} entities.'
    dt = datetime.datetime.now()
    lines = ['999', 'DXF file generated by {}'.format(progname), '999',
             a.format(dt.strftime("%A, %B %d %H:%M")), '999',
             b.format(len(entities)), '  0', 'SECTION', '  2', 'ENTITIES']
    for e in entities:
        if isinstance(e, ent.Contour):
            lines += _dxfcontour(e)
        elif isinstance(e, ent.Arc):
            lines += _dxfarc(e)
        elif isinstance(e, ent.Line):
            lines += ['  0', 'LINE', '  8', 'snijlijnen', ' 10', str(e.x[0]),
                      ' 20', str(e.y[0]), ' 30', '0.0', ' 11', str(e.x[1]),
                      ' 21', str(e.y[1]), ' 31', '0.0', '']
    lines += ['  0', 'ENDSEC', '  0', 'EOF']
    lines.append('')
    with open(name, 'w+') as outf:
        outf.write('\n'.join(lines))


def _get_lines(lines):
    """Generate ent.Line objects from the line in a DXF file.

    :param lines: a list of lines of text
    :returns: a list of ent.Line objects
    """
    idx = [num for num, ln in enumerate(lines) if ln == 'LINE']
    rv = []
    for i in idx:
        num = lines.index("8", i) + 1
        layer = lines[num]
        num = lines.index("10", num) + 1
        x1 = float(lines[num])
        num = lines.index("20", num) + 1
        y1 = float(lines[num])
        num = lines.index("11", num) + 1
        x2 = float(lines[num])
        num = lines.index("21", num) + 1
        y2 = float(lines[num])
        rv.append(ent.Line(x1, y1, x2, y2, i, layer))
    return rv


def _get_arcs(lines):
    """Generate ent.Arc objects from the arcs in a DXF file.

    :param lines: a list of lines of text
    :returns: a list of ent.Arc objects
    """
    idx = [num for num, ln in enumerate(lines) if ln == 'ARC']
    rv = []
    for i in idx:
        num = lines.index("8", i) + 1
        layer = lines[num]
        num = lines.index("10", num) + 1
        cx = float(lines[num])
        num = lines.index("20", num) + 1
        cy = float(lines[num])
        num = lines.index("40", num) + 1
        R = float(lines[num])
        num = lines.index("50", num) + 1
        a1 = math.radians(float(lines[num]))
        num = lines.index("51", num) + 1
        a2 = math.radians(float(lines[num]))
        if a2 < a1:
            a2 += 2*math.pi
        rv.append(ent.Arc(cx, cy, R, a1, a2, i, layer))
    return rv


def _get_circles(lines):
    """Generate closed ent.Arc objects from the circles in a DXF file.

    :param lines: a list of lines of text
    :returns: a list of ent.Arc objects
    """
    idx = [num for num, ln in enumerate(lines) if ln == 'CIRCLE']
    rv = []
    for i in idx:
        num = lines.index("8", i) + 1
        layer = lines[num]
        num = lines.index("10", num) + 1
        cx = float(lines[num])
        num = lines.index("20", num) + 1
        cy = float(lines[num])
        num = lines.index("40", num) + 1
        R = float(lines[num])
        rv.append(ent.Arc(cx, cy, R, 0, 2*math.pi, i, layer))
    return rv


def _get_polylines(lines):
    """Generate ent.Line and ent.Arc objects from the polylines in a DXF file.

    :param lines: a list of lines of text
    :returns: a list of ent.Line and ent.Arc objects
    """
    idx = [num for num, ln in enumerate(lines) if ln == 'POLYLINE']
    rv = []
    for i in idx:
        num = lines.index("8", i) + 1
        layer = lines[num]
        try:
            num = lines.index("70", num) + 1
            closed = int(lines[num]) & 1
        except ValueError:
            closed = False
        end = lines.index('SEQEND', i)
        vi = [num for num, ln in enumerate(lines) if ln == 'VERTEX']
        vi = zip(vi, vi[1:]+[end])
        pnts = []
        angles = []
        for j, k in vi:
            num = lines.index("10", j) + 1
            x = float(lines[num])
            num = lines.index("20", num) + 1
            y = float(lines[num])
            pnts.append((x, y))
            try:
                num = lines.index("42", num) + 1
                if num < k:
                    angles.append(math.atan(float(lines[num]))*4)
                else:
                    angles.append(0)
            except ValueError:
                angles.append(0)
        if closed:
            pnts.append(pnts[0])
        ends = zip(pnts, pnts[1:], angles)
        for sp, ep, a in ends:
            if a == 0:
                rv.append(ent.Line(sp[0], sp[1], ep[0], ep[1], i, layer))
            else:
                (xc, yc), R, a0, a1 = ent.arcdata(sp, ep, a)
                rv.append(ent.Arc(xc, yc, R, a0, a1, i, layer))
    return rv


def _dxfline(e):
    """Generate DXF for a ent.Line

    :param e: nctools.ent.Line
    :returns: a list of lines of text.
    """
    lns = ['  0', 'LINE', '  8', 'snijlijnen', ' 10', str(e.x[0]),
           ' 20', str(e.y[0]), ' 30', '0.0', ' 11', str(e.x[1]),
           ' 21', str(e.y[1]), ' 31', '0.0']
    return lns


def _dxfarc(e):
    """Generate DXF for an ent.Arc

    :param e: nctools.ent.Arc
    :returns: a list of lines of text.
    """
    if not e.ccw:
        e.flip()
    lns = ['  0', 'ARC', '  8', 'snijlijnen', ' 10', str(e.cx),
           ' 20', str(e.cy), ' 30', '0.0', ' 40', str(e.R),
           ' 50', str(math.degrees(e.a[0])),
           ' 51', str(math.degrees(e.a[1]))]
    return lns


def _dxfcontour(e):
    """Generate DXF for a ent.Contour

    :param e: nctools.ent.Contour
    :returns: a list of lines of text.
    """
    lns = []
    for k in e.entities:
        if isinstance(k, ent.Arc):
            lns += _dxfarc(k)
        elif isinstance(k, ent.Line):
            lns += _dxfline(k)
    return lns
