
Run in this order:

1. t1_brain_extract
2. get_fmaps
3. make_designs
4. Run fsl on design scripts
5. make_move_func_templates


Note that the following participants have multiple field maps that must be processed with the corresponding EPI runs:

333
Run 1: fmap A
Runs 2-3: fmap B

343 
Run 1: fmap A
Runs 2-3: flap B

347
Runs 1-2: fmap A
Run 3: fmap B

365
Runs 1-2: fmap A
Run 3: fmap B

366 
Run 1: fmap A
Runs 2-3: fmap B


