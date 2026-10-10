import { Component, Suspense, useEffect, useMemo, useRef, useState, type ReactNode, type ComponentRef } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { Line, OrbitControls, useCursor } from '@react-three/drei'
import { Group, InstancedMesh, Object3D, Vector3, CatmullRomCurve3 } from 'three'
import { Expand, LocateFixed, Minus, Plus, RotateCcw, MapPin, Factory } from 'lucide-react'
import { locations, type LocationId } from '../catalog'

type Vec = [number, number, number]
interface Props { selected: LocationId | null; onSelect: (id: LocationId) => void; available: LocationId[]; animation: number; technology: string; reducedMotion: boolean; progress: number; onProgress: (value: number) => void; focusKey: number; feedSubtype: string }
function Box({ position = [0, 0, 0], size = [1, 1, 1], color, glow = false, rotation = [0, 0, 0] }: { position?: Vec; size?: Vec; color: string; glow?: boolean; rotation?: Vec }) {
  return <mesh position={position} rotation={rotation} castShadow receiveShadow><boxGeometry args={size}/><meshStandardMaterial color={color} roughness={0.74} emissive={glow ? color : '#000000'} emissiveIntensity={glow ? 0.7 : 0}/></mesh>
}
function Cylinder({ position, radius, height, color, glow = false }: { position: Vec; radius: number; height: number; color: string; glow?: boolean }) {
  return <mesh position={position} castShadow receiveShadow><cylinderGeometry args={[radius, radius, height, 12]}/><meshStandardMaterial color={color} roughness={0.6} metalness={0.2} emissive={glow ? color : '#000'} emissiveIntensity={glow ? 0.4 : 0}/></mesh>
}
function Tree({ x, z, scale = 1 }: { x: number; z: number; scale?: number }) {
  return <group position={[x, 0.05, z]} scale={scale}><Box position={[0, 0.34, 0]} size={[0.12, 0.68, 0.12]} color="#75654c"/><mesh position={[0, 0.91, 0]} castShadow><icosahedronGeometry args={[0.49, 0]}/><meshStandardMaterial color="#307957" flatShading/></mesh><mesh position={[0.1, 1.18, 0]} castShadow><icosahedronGeometry args={[0.35, 0]}/><meshStandardMaterial color="#4b9a68" flatShading/></mesh></group>
}
function Streetlight({ x, z }: { x: number; z: number }) {
  return <group position={[x, 0, z]}><Box position={[0, 0.72, 0]} size={[0.045, 1.44, 0.045]} color="#8facae"/><Box position={[0.13, 1.44, 0]} size={[0.28, 0.035, 0.06]} color="#b7c8c6"/><Box position={[0.23, 1.41, 0]} size={[0.14, 0.035, 0.09]} color="#fff0a5" glow/></group>
}
function SolarRoof({ width, depth, y }: { width: number; depth: number; y: number }) {
  return <group position={[0, y, 0]}>{Array.from({ length: 8 }, (_, i) => <Box key={i} position={[(i % 4 - 1.5) * width / 5, 0.025, (Math.floor(i / 4) - 0.5) * depth / 3]} size={[width / 5.6, 0.065, depth / 3.5]} color="#244e69" rotation={[-0.14, 0, 0]}/>)}</group>
}
function Building({ x, z, width, depth, height, color, roof = '#61747f', solar = false }: { x: number; z: number; width: number; depth: number; height: number; color: string; roof?: string; solar?: boolean }) {
  return <group position={[x, 0.1, z]}><Box position={[0, height / 2, 0]} size={[width, height, depth]} color={color}/><Box position={[0, height + 0.03, 0]} size={[width + 0.1, 0.12, depth + 0.1]} color={roof}/>
    {Array.from({ length: Math.max(1, Math.floor(height / 0.45)) * 3 }, (_, i) => <group key={i}><Box position={[(i % 3 - 1) * width / 3.5, 0.32 + Math.floor(i / 3) * 0.45, depth / 2 + 0.013]} size={[width / 5, 0.24, 0.028]} color={i % 3 === 0 ? '#f1db91' : '#376075'} glow={i % 3 === 0}/><Box position={[width / 2 + 0.013, 0.32 + Math.floor(i / 3) * 0.45, (i % 3 - 1) * depth / 3.5]} size={[0.028, 0.24, depth / 5]} color="#4d7b88"/></group>)}
    {solar && <SolarRoof width={width} depth={depth} y={height + 0.13}/>}</group>
}
function Crops() {
  const stalks = useRef<InstancedMesh>(null)
  const heads = useRef<InstancedMesh>(null)
  const count = 180
  useEffect(() => {
    const object = new Object3D()
    for (let i = 0; i < count; i++) {
      const x = (i % 18 - 8.5) * 0.19
      const z = (Math.floor(i / 18) - 4.5) * 0.3
      const h = 0.27 + (i % 5) * 0.025
      object.position.set(x, h / 2 + 0.1, z); object.scale.set(1, h, 1); object.updateMatrix(); stalks.current?.setMatrixAt(i, object.matrix)
      object.position.set(x, h + 0.13, z); object.scale.set(1, 1, 1); object.updateMatrix(); heads.current?.setMatrixAt(i, object.matrix)
    }
    if (stalks.current) stalks.current.instanceMatrix.needsUpdate = true
    if (heads.current) heads.current.instanceMatrix.needsUpdate = true
  }, [])
  return <group><Box position={[0, 0.02, 0]} size={[3.7, 0.12, 3.3]} color="#a69545"/>{Array.from({ length: 11 }, (_, i) => <Box key={i} position={[0, 0.09, (i - 5) * 0.3]} size={[3.7, 0.05, 0.08]} color="#5a723e"/>)}<instancedMesh ref={stalks} args={[undefined, undefined, count]} castShadow><boxGeometry args={[0.035, 1, 0.035]}/><meshStandardMaterial color="#a4b957"/></instancedMesh><instancedMesh ref={heads} args={[undefined, undefined, count]} castShadow><coneGeometry args={[0.065, 0.17, 4]}/><meshStandardMaterial color="#e6c363"/></instancedMesh></group>
}
function Truck({ color = '#57bc8b', moving = false }: { color?: string; moving?: boolean }) {
  return <group scale={moving ? 0.95 : 0.8}><Box position={[0, 0.33, -0.18]} size={[0.47, 0.42, 0.67]} color={color}/><Box position={[0, 0.28, 0.39]} size={[0.47, 0.33, 0.37]} color="#e0e9db"/><Box position={[0, 0.39, 0.54]} size={[0.38, 0.17, 0.02]} color="#347281"/><Box position={[0, 0.13, 0.03]} size={[0.5, 0.12, 1.15]} color="#33494e"/>{[-0.27, 0.27].flatMap(x => [-0.39, 0.38].map(z => <mesh key={`${x}${z}`} position={[x, 0.13, z]} rotation={[0, 0, Math.PI / 2]}><cylinderGeometry args={[0.115, 0.115, 0.1, 10]}/><meshStandardMaterial color="#17292e"/></mesh>))}<Box position={[-0.16, 0.21, 0.59]} size={[0.08, 0.07, 0.02]} color="#ffeabb" glow/><Box position={[0.16, 0.21, 0.59]} size={[0.08, 0.07, 0.02]} color="#ffeabb" glow/></group>
}
function Source({ id, selected, onSelect, available, externalHover }: { id: LocationId; selected: boolean; onSelect: () => void; available: boolean; externalHover: boolean }) {
  const location = locations.find(l => l.id === id)!
  const [hovered, setHovered] = useState(false)
  useCursor(hovered && available)
  return <group position={location.position} onPointerOver={e => { e.stopPropagation(); setHovered(true) }} onPointerOut={() => setHovered(false)} onClick={e => { e.stopPropagation(); if (available) onSelect() }}>
    <mesh position={[0, 0.09, 0]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={id === 'wood' ? [2.5, 1.5] : [4.15, 3.9]}/><meshStandardMaterial color={selected || hovered || externalHover ? '#27675e' : '#46785d'} roughness={1}/></mesh>
    {(selected || hovered || externalHover) && <Line points={id === 'wood' ? [[-1.3, 0.12, -0.8], [1.3, 0.12, -0.8], [1.3, 0.12, 0.8], [-1.3, 0.12, 0.8], [-1.3, 0.12, -0.8]] : [[-2.1, 0.12, -2], [2.1, 0.12, -2], [2.1, 0.12, 2], [-2.1, 0.12, 2], [-2.1, 0.12, -2]]} color={location.color} lineWidth={2}/ >}
    {id === 'paddy' && <><Crops/><group position={[-1.3, 0.13, 1.42]} rotation={[0, Math.PI / 2, 0]}><Truck color="#d4a943"/></group><Box position={[1.65, 0.21, 1.48]} size={[0.45, 0.38, 0.55]} color="#b49b5a"/></>}
    {id === 'food' && <><Building x={0} z={-0.55} width={2.7} depth={1.3} height={1.15} color="#d5b69a" roof="#af6451"/><Box position={[0, 0.76, 0.55]} size={[2.95, 0.1, 0.85]} color="#d36f59"/>{[-1.1, -0.55, 0, 0.55, 1.1].map((x, i) => <group key={x}><Box position={[x, 0.38, 0.73]} size={[0.45, 0.6, 0.45]} color="#897352"/><Box position={[x, 0.71, 0.73]} size={[0.4, 0.07, 0.4]} color={i % 2 ? '#85ab59' : '#df9b56'}/></group>)}<Building x={1.35} z={-1.3} width={0.8} depth={0.65} height={2.5} color="#7499a2"/></>}
    {id === 'paper' && <><Building x={-0.35} z={-0.3} width={2.8} depth={1.9} height={1.35} color="#96b3bf" solar/><Box position={[-0.35, 0.59, 0.7]} size={[1.3, 1.02, 0.08]} color="#547382"/>{Array.from({ length: 9 }, (_, i) => <Box key={i} position={[0.8 + (i % 3) * 0.34, 0.22 + Math.floor(i / 3) * 0.33, 1.15]} size={[0.32, 0.3, 0.5]} color={i % 2 ? '#c2b695' : '#d5c9a9'}/>)}<Box position={[-1.7, 0.15, 1.35]} size={[0.6, 0.25, 0.6]} color="#c2b899"/></>}
    {id === 'plastic' && <><Building x={0.3} z={0.25} width={2.6} depth={1.8} height={0.95} color="#71a0aa" roof="#3b7c96" solar/>{Array.from({ length: 8 }, (_, i) => <Box key={i} position={[-1.3 + (i % 4) * 0.42, 0.28, -1.15 + Math.floor(i / 4) * 0.5]} size={[0.34, 0.4, 0.42]} color={['#69b2c5', '#c9c7bd', '#62ac8d', '#7c91ac'][i % 4]}/>)}<Box position={[-1.2, 0.33, 0.6]} size={[0.8, 0.6, 0.7]} color="#438771"/></>}
    {id === 'wood' && <>{Array.from({ length: 12 }, (_, i) => <mesh key={i} position={[(i % 4 - 1.5) * 0.43, 0.16 + Math.floor(i / 4) * 0.29, 0]} rotation={[Math.PI / 2, 0, 0]} castShadow><cylinderGeometry args={[0.14, 0.14, 1.3, 8]}/><meshStandardMaterial color={i % 2 ? '#b58c5c' : '#926f4c'}/></mesh>)}</>}

  </group>
}
function Plant({ active, technology }: { active: boolean; technology: string }) {
  const biological = ['Anaerobic digestion', 'Landfill gas recovery', 'Fermentation'].includes(technology)
  return <group position={[0, 0, 0.25]}><Box position={[0, 0.08, 0]} size={[3.05, 0.15, 2.5]} color="#a6b8ac"/><Building x={0.45} z={0.17} width={1.8} depth={1.65} height={1.5} color="#c7d8cc" roof="#75a4a6" solar/>
    <Box position={[0.48, 0.75, 1.02]} size={[1.15, 0.75, 0.025]} color="#45877c"/><Box position={[0.48, 1.18, 1.04]} size={[1.15, 0.05, 0.08]} color="#68e0b0" glow/>
    <Cylinder position={[-1, 0.67, -0.42]} radius={0.43} height={1.18} color={active && biological ? '#59efc3' : '#96b6aa'} glow={active && biological}/><Cylinder position={[-1, 1.27, -0.42]} radius={0.44} height={0.12} color="#538780"/>
    <Cylinder position={[-0.75, 0.44, 0.75]} radius={0.29} height={0.75} color={active && !biological ? '#6ce5d3' : '#7caaa4'} glow={active && !biological}/>
    {[-0.2, 0.33].map((x, i) => <group key={x}><Cylinder position={[x, 2.04, -0.43]} radius={0.14} height={1.7} color="#bed2ce"/>{[1.52, 2.03, 2.52].map(y => <Cylinder key={y} position={[x, y, -0.43]} radius={0.145} height={0.22} color={i ? '#568b89' : '#ab7468'}/>)}</group>)}
    <Line points={[[-1, 0.8, -0.42], [-1, 1.48, -0.42], [0, 1.48, -0.42]]} color={active ? '#50e7bc' : '#698e87'} lineWidth={5}/>
    {active && <mesh position={[0, 0.17, 0]} rotation={[-Math.PI / 2, 0, 0]}><ringGeometry args={[1.7, 1.77, 48]}/><meshBasicMaterial color="#51f1cb" transparent opacity={0.65}/></mesh>}

  </group>
}
function Roads() {
  return <group>{[-1.9, 1.9].map(x => <group key={x}><Box position={[x, 0.08, 0]} size={[0.88, 0.1, 14.5]} color="#354952"/><Box position={[x - 0.5, 0.07, 0]} size={[0.14, 0.13, 14.5]} color="#90a6a1"/><Box position={[x + 0.5, 0.07, 0]} size={[0.14, 0.13, 14.5]} color="#90a6a1"/>{Array.from({ length: 19 }, (_, i) => <Box key={i} position={[x, 0.14, (i - 9) * 0.72]} size={[0.025, 0.01, 0.3]} color="#a9b8ab"/>)}</group>)}{[-1.7, 1.7].map(z => <group key={z}><Box position={[0, 0.09, z]} size={[14.5, 0.1, 0.88]} color="#354952"/>{[-0.5, 0.5].map(d => <Box key={d} position={[0, 0.08, z + d]} size={[14.5, 0.13, 0.12]} color="#90a6a1"/>)}{Array.from({ length: 19 }, (_, i) => <Box key={i} position={[(i - 9) * 0.72, 0.15, z]} size={[0.3, 0.01, 0.025]} color="#a9b8ab"/>)}</group>)}{[-1.9, 1.9].flatMap(x => [-1.7, 1.7].map(z => <group key={`${x}${z}`}>{Array.from({ length: 5 }, (_, i) => <Box key={i} position={[x + (i - 2) * 0.15, 0.17, z + 0.65]} size={[0.08, 0.01, 0.35]} color="#d0d2b8"/>)}</group>))}</group>
}
type ControlsRef = ComponentRef<typeof OrbitControls>
function deliveryPath(selected: LocationId | null) {
  const docks: Record<LocationId, Vec> = { paddy: [-3.3, .18, -2.1], food: [3.1, .18, -2.1], paper: [-3.3, .18, 2.1], plastic: [3.1, .18, 2.1], wood: [0, .18, -5.2] }
  const start = docks[selected || 'paddy']
  const points: Vec[] = selected === 'wood' ? [start, [1.9, .18, -5.2], [1.9, .18, -1.7], [-1.9, .18, -1.7], [-1.9, .18, 1.7], [0, .18, 1.7]] : [start, [start[0], .18, start[2] < 0 ? -1.7 : 1.7], [-1.9, .18, start[2] < 0 ? -1.7 : 1.7], [-1.9, .18, 1.7], [0, .18, 1.7]]
  return points.filter((p, i) => i === 0 || p.some((v, n) => v !== points[i - 1][n])).map(p => new Vector3(...p))
}
function Delivery({ selected, animation, reducedMotion, onProgress }: Pick<Props, 'selected' | 'animation' | 'reducedMotion' | 'onProgress'>) {
  const group = useRef<Group>(null)
  const elapsed = useRef(0)
  const reported = useRef(-1)
  const { invalidate, gl } = useThree()
  const curve = useMemo(() => new CatmullRomCurve3(deliveryPath(selected), false, 'centripetal', .12), [selected])
  useEffect(() => { elapsed.current = 0; reported.current = -1; if (animation) { onProgress(0); invalidate() } }, [animation, invalidate, onProgress])
  useFrame((_, delta) => {
    gl.domElement.dataset.animationState = `${animation}:${Boolean(group.current)}`
    if (!group.current || !animation) return
    elapsed.current += Math.min(delta, .25)
    const progress = reducedMotion ? 1 : Math.min(1, elapsed.current / 6.4)
    const drive = Math.min(1, progress / .4)
    const point = curve.getPointAt(drive)
    const tangent = curve.getTangentAt(Math.min(.999, drive))
    group.current.position.copy(point)
    const angle = Math.atan2(tangent.x, tangent.z)
    const difference = Math.atan2(Math.sin(angle - group.current.rotation.y), Math.cos(angle - group.current.rotation.y))
    group.current.rotation.y += difference * (1 - Math.exp(-delta * 14))
    gl.domElement.dataset.truckPosition = point.toArray().map(v => v.toFixed(2)).join(',')
    if (progress - reported.current >= .025 || (progress === 1 && reported.current < 1)) { reported.current = progress; onProgress(progress) }
    if (progress < 1) invalidate()
  })
  return <><group ref={group} visible={animation > 0}><Truck moving/></group>{animation > 0 && <Line points={deliveryPath(selected)} color="#47d0b2" lineWidth={3} dashed dashScale={4} dashSize={.3} gapSize={.2}/>}</>
}
function AnimationWakeup({ animation }: { animation: number }) {
  const { invalidate } = useThree()
  useEffect(() => {
    if (!animation) return
    let request = 0
    const start = performance.now()
    const wake = () => { invalidate(); if (performance.now() - start < 9000) request = requestAnimationFrame(wake) }
    request = requestAnimationFrame(wake)
    return () => cancelAnimationFrame(request)
  }, [animation, invalidate])
  return null
}
function CameraRig({ selected, focusKey, action, reducedMotion, controls }: Pick<Props, 'selected' | 'focusKey' | 'reducedMotion'> & { action: { key: number; type: string }; controls: React.RefObject<ControlsRef | null> }) {
  const { camera, size, invalidate, gl } = useThree()
  const target = useRef(new Vector3())
  const position = useRef(new Vector3(18, 16, 19))
  const zoom = useRef(34)
  const moving = useRef(false)
  const fit = Math.min(size.width / 21.3, size.height / 13.8, 52)
  useEffect(() => {
    target.current.set(0, .25, 0); position.current.set(18, 16, 19); zoom.current = fit; moving.current = true; invalidate()
  }, [size.width, size.height, fit, invalidate])
  useEffect(() => {
    if (!focusKey) return
    const source = locations.find(l => l.id === selected)
    target.current.set(source ? source.position[0] * .22 : 0, .35, source ? source.position[2] * .22 : 0)
    position.current.copy(target.current).add(new Vector3(18, 16, 19)); zoom.current = fit * 1.04; moving.current = true; invalidate()
  }, [focusKey, selected, fit, invalidate])
  useEffect(() => {
    if (action.type === 'reset') { target.current.set(0, .25, 0); position.current.set(18, 16, 19); zoom.current = fit }
    else { target.current.copy(controls.current?.target || new Vector3()); position.current.copy(camera.position); zoom.current = Math.max(10, Math.min(70, camera.zoom * (action.type === 'in' ? 1.15 : 1 / 1.15))) }
    moving.current = true; invalidate()
  }, [action, camera, controls, fit, invalidate])
  useEffect(() => {
    const control = controls.current; const cancel = () => { moving.current = false }
    control?.addEventListener('start', cancel); return () => control?.removeEventListener('start', cancel)
  }, [controls])
  useFrame((_, delta) => {
    if (moving.current) {
      const blend = reducedMotion ? 1 : 1 - Math.exp(-delta * 7)
      camera.position.lerp(position.current, blend)
      camera.zoom += (zoom.current - camera.zoom) * blend
      controls.current?.target.lerp(target.current, blend)
      camera.updateProjectionMatrix(); controls.current?.update()
      moving.current = camera.position.distanceTo(position.current) > .005 || Math.abs(camera.zoom - zoom.current) > .005
      if (moving.current) invalidate()
    }
    gl.domElement.dataset.cameraTransform = [...camera.position.toArray(), camera.zoom].map(v => v.toFixed(2)).join(',')
  })
  return null
}
function CityDetails({ active }: { active: boolean }) {
  return <group>
    {[-6.65, 6.65].map(x => <group key={x}><Box position={[x, .06, 0]} size={[.65, .07, 14.1]} color="#3b515b"/>{Array.from({ length: 19 }, (_, i) => <Box key={i} position={[x, .11, (i - 9) * .7]} size={[.025, .01, .26]} color="#abb9ad"/>)}</group>)}
    {[-6.65, 6.65].map(z => <group key={z}><Box position={[0, .06, z]} size={[14.1, .07, .65]} color="#3b515b"/>{Array.from({ length: 19 }, (_, i) => <Box key={i} position={[(i - 9) * .7, .11, z]} size={[.26, .01, .025]} color="#abb9ad"/>)}</group>)}
    <Box position={[.8, .07, -5.2]} size={[2, .06, .42]} color="#65776a"/>
    <Building x={2.95} z={-6} width={1.3} depth={.8} height={2.4} color="#b6bfb5" roof="#839ca5" solar/><Building x={4.3} z={-6.1} width={1.15} depth={.8} height={1.85} color="#bc9f83"/>
    <Building x={-5.3} z={5.5} width={1.5} depth={1.05} height={.8} color="#bdc7b3" solar/><Building x={-3.6} z={5.6} width={1.35} depth={.85} height={1.35} color="#7e9ba3"/>
    <Building x={5.1} z={5.7} width={1.7} depth={.8} height={1.45} color="#a7bfc7" roof="#567e92" solar/><Building x={3.25} z={5.85} width={1.4} depth={.6} height={.85} color="#bda27a"/>
    <Building x={-4.7} z={-6} width={1.4} depth={.75} height={.65} color="#cdbd93" roof="#7f825c"/>
    <Cylinder position={[-6, .6, -5.9]} radius={.31} height={1.1} color="#b6bdad"/>
    {[[-5.2, 1.12],[-4,1.12],[4.1,1.12],[5.4,1.12]].map(([x,z],i) => <group key={x}><Box position={[x,.22,z]} size={[.58,.3,.32]} color={i % 2 ? '#649d7c' : '#a39263'}/><Box position={[x,.4,z]} size={[.64,.07,.38]} color="#83ad96"/></group>)}
    <group position={[-5.9,.16,5.3]} rotation={[0,Math.PI/2,0]}><Truck color="#c2aa72"/></group>
    <group position={[4.8,.16,6.65]} rotation={[0,-Math.PI/2,0]}><Truck color="#698ca6"/></group>
    {Array.from({length:12},(_,i)=><Box key={i} position={[2.6+(i%4)*.19,.23+Math.floor(i/4)*.18,4.9]} size={[.17,.17,.4]} color={['#6ba9b4','#aab6b5','#549276'][i%3]}/>)}
    {Array.from({length:6},(_,i)=><Box key={i} position={[-6.05+(i%3)*.3,.22+Math.floor(i/3)*.3,4.7]} size={[.28,.27,.42]} color="#c4b48a"/>)}
    {[-.9,-.4,.1,.6].map(x=><Box key={x} position={[x,.13,3.9]} size={[.29,.09,.06]} color="#b3c6bb"/>)}
    <Box position={[0,.12,3.5]} size={[2.5,.1,1.1]} color="#597e61"/>
    {[-.8,.75].map(x=><Tree key={x} x={x} z={3.5} scale={.5}/>)}
    <Box position={[-1.15,.28,1.05]} size={[.42,.3,.75]} color="#c1d2bd"/><Box position={[-1.15,.47,1.05]} size={[.5,.09,.84]} color={active?'#6fecc0':'#789e90'} glow={active}/>
    <Cylinder position={[1.3,.65,-.8]} radius={.21} height={1.05} color="#82aaa4"/><Cylinder position={[1.3,1.22,-.8]} radius={.24} height={.12} color="#5f8e87"/>
    <Line points={[[1.3,1,-.8],[1.3,1.65,-.8],[.7,1.65,-.8]]} color={active?'#64e1c1':'#8ca99f'} lineWidth={4}/>
    <Box position={[.52,.17,1.21]} size={[1.03,.13,.24]} color="#4a716f"/>
    {Array.from({length:4},(_,i)=><Cylinder key={i} position={[-.07+i*.27,.34,1.28]} radius={.07} height={.23} color={active?'#76e8c6':'#98bcb2'}/>)}
  </group>
}
function EquipmentMotion({ active }: { active: boolean }) {
  const rotor=useRef<Group>(null)
  const {invalidate}=useThree()
  useFrame((_,delta)=> {if(!active||!rotor.current)return;rotor.current.rotation.z+=delta*2;invalidate()})
  return <group ref={rotor} position={[-.76,.73,.89]}><mesh rotation={[Math.PI/2,0,0]}><torusGeometry args={[.21,.025,6,20]}/><meshStandardMaterial color={active?'#7cf2d0':'#acc6bc'} metalness={.55} roughness={.4}/></mesh><Box size={[.33,.045,.04]} color="#b4c9c2"/><Box size={[.045,.33,.04]} color="#b4c9c2"/></group>
}
function Environment(props: Props & { hovered: LocationId | null }) {
  return <><ambientLight intensity={.85}/><hemisphereLight args={['#d8f2f8', '#548475', 1.35]}/><directionalLight position={[-5, 14, 8]} intensity={3.1} castShadow shadow-mapSize={[1536, 1536]} shadow-camera-left={-12} shadow-camera-right={12} shadow-camera-top={12} shadow-camera-bottom={-12} shadow-bias={-0.0004}/>
    <group><Box position={[0, -0.55, 0]} size={[15.7, 0.95, 15.7]} color="#234e47"/><Box position={[0, -0.05, 0]} size={[15.7, 0.12, 15.7]} color="#528063"/><Box position={[0, -1.08, 0]} size={[16.05, 0.1, 16.05]} color="#27736d"/>
    <Roads/>{locations.map(l => <Source key={l.id} id={l.id} selected={props.selected === l.id} onSelect={() => props.onSelect(l.id)} available={props.available.includes(l.id)} externalHover={props.hovered === l.id}/>)}<Plant active={props.animation > 0 && props.progress >= .4} technology={props.technology}/>
    {Array.from({ length: 30 }, (_, i) => { const side = i % 4; const n = (Math.floor(i / 4) - 3) * 1.8; return <Tree key={i} x={side === 0 ? -7.1 : side === 1 ? 7.1 : n} z={side === 2 ? -7.1 : side === 3 ? 7.1 : n} scale={0.8 + (i % 3) * 0.14}/> })}
    {[[-2.6, -2.4], [2.6, -2.5], [-2.6, 2.6], [2.6, 2.5], [-5.8, 0], [5.8, 0], [0, 5.8]].map(([x, z]) => <Tree key={`${x}${z}`} x={x} z={z} scale={0.85}/>)}
    {[-6, -3.4, 3.4, 6].flatMap(n => [-1.3, 2.5].map(x => <Streetlight key={`${n}${x}`} x={x} z={n}/>))}
    <Building x={-4.7} z={0} width={1.5} depth={0.8} height={0.85} color="#b6c7b4" solar/><Building x={4.9} z={0} width={1.6} depth={0.8} height={0.9} color="#b3c5b8"/>
    <Box position={[0, 0.11, 5.3]} size={[2.7, 0.08, 2.1]} color="#427e93"/><Box position={[0, 0.16, 5.3]} size={[2.3, 0.05, 1.7]} color="#4a9cb1"/><Tree x={-0.9} z={6.6} scale={0.6}/><Tree x={0.8} z={6.6} scale={0.8}/>
    <group position={[4.7, 0.17, -1.7]} rotation={[0, Math.PI / 2, 0]}><Truck color="#bdc2aa"/></group><group position={[1.9, 0.17, 5.3]}><Truck color="#609eb7"/></group>
    <CityDetails active={props.animation > 0 && props.progress >= .4}/><EquipmentMotion active={props.animation > 0 && props.progress >= .4 && props.progress < 1}/><Delivery selected={props.selected} animation={props.animation} reducedMotion={props.reducedMotion} onProgress={props.onProgress}/></group>
  </>
}
type PinPositions = Record<LocationId | 'plant', { x: number; y: number; visible: boolean }>
function PinProjection({ onProject }: { onProject: (positions: PinPositions) => void }) {
  const { camera, size } = useThree()
  const previous = useRef('')
  useFrame(() => {
    camera.updateMatrixWorld()
    const entries = [...locations.map(l => ({ id: l.id, position: [l.position[0], l.id === 'wood' ? 1.9 : 2.8, l.position[2]] })), { id: 'plant', position: [0.3, 3.45, 0.55] }]
    const next = Object.fromEntries(entries.map(pin => {
      const point = new Vector3(...pin.position).project(camera)
      return [pin.id, { x: Math.round((point.x + 1) * size.width * 5) / 10, y: Math.round((1 - point.y) * size.height * 5) / 10, visible: point.z >= -1 && point.z <= 1 }]
    })) as PinPositions
    const signature = JSON.stringify(next)
    if (signature !== previous.current) { previous.current = signature; onProject(next) }
  })
  return null
}
class SceneBoundary extends Component<{ children: ReactNode; fallback: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  render() { return this.state.failed ? this.props.fallback : this.props.children }
}
function webglAvailable() {
  try { const c = document.createElement('canvas'); const gl = c.getContext('webgl2'); if (!gl) return false; gl.getExtension('WEBGL_lose_context')?.loseContext(); return true } catch { return false }
}
export default function CityScene(props: Props) {
  const [webgl] = useState(webglAvailable)
  const [pinPositions, setPinPositions] = useState<PinPositions | null>(null)
  const [lost, setLost] = useState(false)
  const [hovered, setHovered] = useState<LocationId | null>(null)
  const controls = useRef<ControlsRef>(null)
  const [action, setAction] = useState({ key: 0, type: 'reset' })
  const container = useRef<HTMLDivElement>(null)
  const [fullscreenError, setFullscreenError] = useState('')
  const fallback = <div className="scene-fallback" data-testid="webgl-fallback"><LocateFixed size={32}/><h3>The city is in map mode</h3><p>3D rendering is unavailable on this device. Select a source below; all API calculations remain available.</p><div>{locations.map(l => <button key={l.id} type="button" disabled={!props.available.includes(l.id)} onClick={() => props.onSelect(l.id)}>{l.title}</button>)}</div></div>
  return <div className="city-viewport" ref={container} aria-label="Interactive miniature waste collection city"><div className="city-topline"><span className="live-badge"><span/> CIRCULAR CITY</span><span className="scene-label">ISOMETRIC EXPLORER / 01</span></div>
    {webgl && !lost ? <SceneBoundary fallback={fallback}><Suspense fallback={<div className="scene-fallback">Preparing the city...</div>}><Canvas frameloop="demand" orthographic shadows dpr={[1, 1.5]} camera={{ position: [18, 16, 19], zoom: 34, near: 0.1, far: 100 }} gl={{ antialias: true, alpha: true }} onCreated={({ gl }) => { gl.domElement.addEventListener('webglcontextlost', e => { e.preventDefault(); setLost(true) }, { once: true }) }}><Environment {...props} hovered={hovered}/><AnimationWakeup animation={props.animation}/><PinProjection onProject={setPinPositions}/><CameraRig action={action} selected={props.selected} focusKey={props.focusKey} controls={controls} reducedMotion={props.reducedMotion}/><OrbitControls ref={controls} makeDefault enablePan={false} enableDamping dampingFactor={0.08} minZoom={10} maxZoom={65} minPolarAngle={0.55} maxPolarAngle={1.15} target={[0, .25, 0]}/></Canvas></Suspense></SceneBoundary> : fallback}
    {webgl && !lost && pinPositions && <div className="pin-overlay">{locations.map(location => {
      const point = pinPositions[location.id]
      const tooltip = hovered === location.id
      return <div key={location.id} className="projected-pin" style={{ transform: `translate3d(${point.x}px, ${point.y}px, 0) translate(-50%, -50%)`, display: point.visible ? 'block' : 'none' }}><button type="button" className={`compact-pin ${props.selected === location.id ? 'selected' : ''}`} style={{ '--pin-color': location.color } as React.CSSProperties} disabled={!props.available.includes(location.id)} aria-label={`Select ${location.title} on map`} aria-pressed={props.selected === location.id} onMouseEnter={() => setHovered(location.id)} onMouseLeave={() => setHovered(null)} onFocus={() => setHovered(location.id)} onBlur={() => setHovered(null)} onClick={() => props.onSelect(location.id)}><MapPin size={18}/></button>{tooltip && <div className="pin-tooltip" role="tooltip"><strong>{location.title}</strong><span>{props.selected === location.id ? props.feedSubtype : location.preferredSubtype}</span><small>{location.weight} kg illustrative default</small></div>}</div>
    })}<div className="projected-pin plant-pin" style={{ transform: `translate3d(${pinPositions.plant.x}px, ${pinPositions.plant.y}px, 0) translate(-50%, -50%)` }}><div className={`hub-pin ${props.animation && props.progress >= .4 ? 'active' : ''}`} title="Central processing hub / conceptual"><Factory size={19}/></div></div></div>}
    <div className="map-tools"><button aria-label="Zoom in" onClick={() => setAction(a => ({ key: a.key + 1, type: 'in' }))}><Plus size={17}/></button><button aria-label="Zoom out" onClick={() => setAction(a => ({ key: a.key + 1, type: 'out' }))}><Minus size={17}/></button><button aria-label="Reset isometric camera" onClick={() => setAction(a => ({ key: a.key + 1, type: 'reset' }))}><RotateCcw size={16}/></button><button aria-label="Expand city view" onClick={() => { if (!document.fullscreenElement) { container.current?.requestFullscreen().catch(() => setFullscreenError('Fullscreen is unavailable in this browser.')) } else { void document.exitFullscreen() } }}><Expand size={16}/></button></div>
    <div className="city-bottomline"><span><span className="legend-dot"/> Click a pin to select a waste source</span><span>Drag to orbit / Scroll to zoom</span></div>{fullscreenError && <span className="scene-error" role="status">{fullscreenError}</span>}
  </div>
}
