"""Blender product shot: base with PCB inside, lid lifted above.
blender -b -P render_product.py -- <pcb.glb> <base.stl> <lid.stl> <out.png> [samples]
All geometry in mm frame of enclosure.py (scaled to metres in Blender)."""
import bpy, sys, math, mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
GLB, BASE, LID, OUT = argv[:4]
SAMPLES = int(argv[4]) if len(argv) > 4 else 96
RES = (int(argv[5]), int(argv[6])) if len(argv) > 6 else (1800, 1350)
MM = 0.001

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.length_unit = 'MILLIMETERS'


def mat(name, color, rough=0.5, metal=0.0, trans=0.0, sss=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if trans:
        b.inputs["Transmission Weight"].default_value = trans
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    return m


def srgb(h):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


# ---- PCB
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=GLB)
pcb_objs = [o for o in bpy.data.objects if o not in before]
root = bpy.data.objects.new("PCB", None)
sc.collection.objects.link(root)
for o in pcb_objs:
    if o.parent is None:
        o.parent = root
bpy.context.view_layer.update()
# measure and normalise to metres in our mm frame (board X 0..24, Y -34..0, Z 0..1.6)
pts = []
for o in pcb_objs:
    if o.type == 'MESH':
        pts += [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
mn = mathutils.Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
mx = mathutils.Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
print("PCB bbox", mn, mx)
size_x = mx.x - mn.x
scale = (24.0 * MM) / size_x
root.scale = (scale, scale, scale)
bpy.context.view_layer.update()
pts = []
for o in pcb_objs:
    if o.type == 'MESH':
        pts += [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
mn = mathutils.Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
# board body bottom should land at z=0; x=0; y=-34 mm
root.location = (root.location.x - mn.x, root.location.y - mn.y - 34 * MM, root.location.z - mn.z)
bpy.context.view_layer.update()

# module RF can: Espressif's STEP comes in white -> brushed steel
for o in pcb_objs:
    if o.type == 'MESH':
        ws = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
        dx = max(p.x for p in ws) - min(p.x for p in ws); dy = max(p.y for p in ws) - min(p.y for p in ws)
        top = max(p.z for p in ws)
        if dx > 0.010 and dy > 0.008 and top > 0.0035 and top < 0.0045:
            for slot in o.material_slots:
                slot.material = mat("can", srgb("#d5d8dd"), rough=0.5, metal=1.0)

# missing models: JST PA header (white nylon) and USB-C receptacle (steel)
def cube(name, x0, x1, y0, y1, z0, z1, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object
    o.name = name
    o.scale = ((x1 - x0) * MM, (y1 - y0) * MM, (z1 - z0) * MM)
    o.location = ((x0 + x1) / 2 * MM, (y0 + y1) / 2 * MM, (z0 + z1) / 2 * MM)
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        bv = o.modifiers.new("b", 'BEVEL'); bv.width = bevel * MM; bv.segments = 3
    o.data.materials.append(m)
    return o

nylon = mat("nylon", srgb("#efeee6"), rough=0.55)
steel = mat("steel", srgb("#c9ccd1"), rough=0.25, metal=1.0)
pin = mat("pin", srgb("#d4af37"), rough=0.3, metal=1.0)
dark = mat("hole", (0.015, 0.015, 0.015), 0.9)
gold = pin
# JST PA S05B-PASK-2 (side entry): nylon shroud, open front with 5 contact cavities, latch ramp on top
cube("J1_back", 11.5, 23.5, -27.0, -22.3, 1.6, 8.1, nylon, 0.25)
cube("J1_floor", 11.5, 23.5, -34.0, -27.0, 1.6, 2.4, nylon, 0.15)
cube("J1_roof", 11.5, 23.5, -34.0, -27.0, 7.3, 8.1, nylon, 0.15)
cube("J1_wl", 11.5, 12.3, -34.0, -27.0, 2.4, 7.3, nylon, 0.1)
cube("J1_wr", 22.7, 23.5, -34.0, -27.0, 2.4, 7.3, nylon, 0.1)
cube("J1_cavity", 12.3, 22.7, -33.0, -27.0, 2.4, 7.3, dark)
for i in range(5):
    x = 13.5 + 2.0 * i
    cube("J1_pin%d" % i, x - 0.32, x + 0.32, -33.2, -27.0, 3.2, 3.84, gold, 0.05)
cube("J1_latch", 15.5, 19.5, -33.6, -30.5, 8.1, 8.6, nylon, 0.15)
# USB-C receptacle: stadium shell, black cavity with tongue
def stadium(name, cx, cz, w, h, y0, y1, m, n=24):
    """Manifold prism with a stadium (rounded-slot) cross-section, extruded along Y."""
    r = h / 2
    outline = []
    for k in range(n + 1):                      # right half-circle
        a = -math.pi / 2 + math.pi * k / n
        outline.append((cx + w / 2 - r + r * math.cos(a), cz + r * math.sin(a)))
    for k in range(n + 1):                      # left half-circle
        a = math.pi / 2 + math.pi * k / n
        outline.append((cx - w / 2 + r + r * math.cos(a), cz + r * math.sin(a)))
    N = len(outline)
    verts = [(x * MM, y0 * MM, z * MM) for x, z in outline] + [(x * MM, y1 * MM, z * MM) for x, z in outline]
    faces = [list(range(N))[::-1], list(range(N, 2 * N))]
    faces += [[i, (i + 1) % N, N + (i + 1) % N, N + i] for i in range(N)]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    me.validate(); me.calc_normals() if hasattr(me, "calc_normals") else None
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    o.data.materials.append(m)
    return o

shell = stadium("USB", 5.4, 3.23, 8.94, 3.26, -34.0, -26.7, steel)
cutter = stadium("USBcut", 5.4, 3.23, 8.34, 2.66, -35.0, -28.5, dark)
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = cutter; cutter.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.objects.active = shell; shell.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
bm = shell.modifiers.new("cut", 'BOOLEAN'); bm.operation = 'DIFFERENCE'; bm.object = cutter; bm.solver = 'EXACT'
bpy.ops.object.modifier_apply(modifier="cut")
bpy.data.objects.remove(cutter)
for p in shell.data.polygons:
    p.use_smooth = True
stadium("USBback", 5.4, 3.23, 8.3, 2.6, -28.6, -28.45, dark)
cube("USB_tongue", 2.1, 8.7, -33.5, -28.5, 2.9, 3.56, mat("tongue", (0.03, 0.03, 0.035), 0.6), 0.1)
for i in range(12):
    x = 2.6 + i * 0.5
    cube("USB_c%d" % i, x, x + 0.25, -33.3, -28.5, 3.56, 3.62, gold)

# ---- enclosure
petg = mat("petg", srgb("#2b2f36"), rough=0.38, coat=0.15)
petg_lid = mat("petg_lid", srgb("#2b2f36"), rough=0.38, coat=0.15)


def stl(path, name, m):
    bpy.ops.wm.stl_import(filepath=path)
    o = bpy.context.object
    o.name = name
    o.data.transform(mathutils.Matrix.Scale(MM, 4))
    o.data.materials.append(m)
    return o

base = stl(BASE, "base", petg)
lid = stl(LID, "lid", petg_lid)
for o in (base, lid):
    for p in o.data.polygons:
        p.use_smooth = False
lid.location = (-42 * MM, 30 * MM, -4.0 * MM)   # closed lid standing behind-left of the open base
lid.rotation_euler = (0, 0, math.radians(18))

# ---- antenna coax from U.FL (7.1, -2.25) out of the back slot, plus flex antenna
crv = bpy.data.curves.new("coax", 'CURVE'); crv.dimensions = '3D'
sp = crv.splines.new('BEZIER'); pts3 = [(7.1, -2.25, 5.0), (7.1, 1.2, 5.8), (12.0, 5.5, 2.0), (26.0, 3.0, -3.9), (33.0, -3.0, -3.9)]
sp.bezier_points.add(len(pts3) - 1)
for bp, p in zip(sp.bezier_points, pts3):
    bp.co = mathutils.Vector(p) * MM; bp.handle_left_type = bp.handle_right_type = 'AUTO'
crv.bevel_depth = 0.55 * MM; crv.bevel_resolution = 4
co = bpy.data.objects.new("coax", crv); sc.collection.objects.link(co)
co.data.materials.append(mat("coaxm", srgb("#1a1a1a"), 0.45))
ant = cube("antenna", 33.0, 65.0, -7.5, 0.5, -4.6, -4.35, mat("flex", srgb("#b8732e"), 0.35, 0.0, coat=0.6))
cube("ufl", 6.1, 8.1, -3.25, -1.25, 4.0, 5.2, pin, 0.3)

# ---- studio
bpy.ops.mesh.primitive_plane_add(size=1)
floor = bpy.context.object
floor.scale = (1.2, 1.2, 1)
floor.location = (0.012, 0.0, -4.6 * MM)
floor.data.materials.append(mat("floor", srgb("#e9e9ec"), 0.6))
# sweep (curved backdrop)
bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=1.2, location=(0.012, 0.25 + 0.05, 0.25 - 0.0046),
                                    rotation=(0, math.radians(90), 0))
bd = bpy.context.object
bd.data.materials.append(mat("bd", srgb("#e9e9ec"), 0.6))
bd.hide_render = True


def area(name, loc, rot, size, energy, color=(1, 1, 1)):
    l = bpy.data.lights.new(name, 'AREA'); l.size = size; l.energy = energy; l.color = color
    o = bpy.data.objects.new(name, l); o.location = loc; o.rotation_euler = rot
    sc.collection.objects.link(o)
    return o

area("key", (-0.08, -0.10, 0.16), (math.radians(40), 0, math.radians(-35)), 0.15, 1.6)
area("fill", (0.16, -0.06, 0.08), (math.radians(60), 0, math.radians(60)), 0.2, 0.5)
area("rim", (0.02, 0.18, 0.12), (math.radians(-50), 0, math.radians(180)), 0.1, 1.2)
world = bpy.data.worlds.new("w"); sc.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.9, 0.9, 0.92, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.12

# ---- camera
cam = bpy.data.cameras.new("cam"); cam.lens = 90
camo = bpy.data.objects.new("cam", cam); sc.collection.objects.link(camo); sc.camera = camo
target = mathutils.Vector((6.0 * MM, -2.0 * MM, 2.0 * MM))
camo.location = target + mathutils.Vector((0.026, -0.205, 0.138))
d = target - camo.location
camo.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
focus = mathutils.Vector((12.0 * MM, -30.0 * MM, 4.0 * MM))
cam.dof.use_dof = False; cam.dof.focus_distance = (focus - camo.location).length; cam.dof.aperture_fstop = 22

sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = False
sc.render.resolution_x, sc.render.resolution_y = RES
sc.view_settings.view_transform = 'AgX' if 'AgX' in [v.identifier for v in sc.view_settings.bl_rna.properties['view_transform'].enum_items] else 'Filmic'
sc.view_settings.look = 'None'
sc.render.film_transparent = False
sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("rendered", OUT)
