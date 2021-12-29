import gl
from pathlib import Path
import json


mother_dir = Path(
    "/home/groot/Projects/PhD/connectomeplasticity/src/connectome_plasticity_project/statistics"
)
for d in mother_dir.glob("*/tmp_5.nii.gz"):
    for elev in [180, 0]:
        print(d.name)
        gl.resetdefaults()
        gl.azimuthelevation(70, 15)

        gl.meshload(
            "/media/groot/Data/Parcellations/FreeSurfer5.3/fsaverage/surf/lh.pial"
        )

        gl.overlayload(str(d))
        gl.overlaycolorname(2, "Blue-Cyan")
        gl.overlayminmax(2, -2, 2)
        gl.overlaytransparencyonbackground(0)
        gl.meshcurv()
        gl.hemispheredistance(1)
        gl.hemispherepry(100)
        gl.azimuthelevation(elev, 0)
        gl.cameradistance(1.6)
        gl.savebmp(
            str(d.with_name(f"{d.name.split('.')[0]}_{elev}_surface.png"))
        )
