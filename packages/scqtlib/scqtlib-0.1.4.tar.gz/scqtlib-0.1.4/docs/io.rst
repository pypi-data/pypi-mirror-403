============
IO interface
============

dropEst data
============
DropEst_ (`-V`) generates intron, exon, and spanning count matrices stored in 
an RDS file. Here, we provide a two-step way to convert it into AnnData for 
using scanpy.

1. using convert_dropEst.R_ from command line to match genes among three 
   matrices and save to standard .mtx files in the same folder:

   .. code-block:: bash

       Rscript convert_dropEst.R FULL_PATH_matrices.rds

2. load these three matrices as AnnData in Python:

   .. code-block:: python

      import scqtlib
      adata = scqtlib.io.read_dropEst(YOUR_DIRECTORY_PATH)


.. _DropEst: https://dropest.readthedocs.io/en/latest/dropest.html#velocyto-integration
.. _convert_dropEst.R: https://github.com/huangyh09/scQTLib/blob/master/misc/convert_dropEst.R