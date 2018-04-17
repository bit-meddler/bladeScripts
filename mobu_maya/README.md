# Just some MoCap Helpers for MoBu & Maya

## skel save/restore
saves the pose, DoF locks, and limits of an arbitrary skeleton then restores it.  Nieve but good to get you our of a... Pickle
```
(*_*)
( *_*)>¬0-0
(¬0_0)
```

## arnold2Basic
Down-convert an Arnold Shader to a basic Type (like Blinn, Phong, Lambert).

## footFudger
Copy and key a _source_ node's transform onto a _target_ node.  Key for selected play-range.  Select order is like parenting: child (target), then parent (source).

## MoBu Scene-Clean
Cleans a MoBu scene for export back into Maya (_wip_)

## Null-From-Joint
Drop a NULL (Locator) in 3D Space on a keypress / event.  3D pos comes from a joint.  Example use: A prop or peice of scenery is on stage and we need to record it's dimentions in MoBu to rough in some geo. (_wip_)