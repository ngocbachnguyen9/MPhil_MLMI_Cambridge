#!/bin/bash
#SBATCH -A MLMI-as3159-SL2-GPU
#SBATCH -J mwnlud
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --time=2:00:00
#SBATCH --mail-type=FAIL
#! Uncomment this to prevent the job from being requeued (e.g. if
#! interrupted by node failure or system downtime):
##SBATCH --no-requeue
#SBATCH -p ampere
#! ############################################################
. /etc/profile.d/modules.sh                # Leave this line (enables the module command)
module purge                               # Removes all modules still loaded
module load rhel8/default-amp
module load cuda/11.1 intel/mkl/2017.4
export OMP_NUM_THREADS=1
source /rds/project/rds-xyBFuSj0hm0/MLMI8.L2022/envs/README.MLMI8.GPT2DST.activate

##
JOBID=$SLURM_JOB_ID
LOG=slurm_logs/decode-log.$JOBID
ERR=slurm_logs/decode-err.$JOBID

mkdir -p slurm_logs

echo -e "JobID: $JOBID\n======" > $LOG
echo "Time: `date`" >> $LOG
echo "Running on master node: `hostname`" >> $LOG
echo "python `which python`": >> $LOG

CHECKPOINT=/rds/user/as3159/hpc-work/checkpoints/nlu_continued_training/model.200000/

if [ -z ${CHECKPOINT+x} ]; then
    echo "["${value}"] Prepend the CHECKPOINT=model_path variable to the command."
    exit 1
fi

DST_ARGS=$BDIR/decode_arguments.nlu.mwoz21.yaml

# decode the development set (NEW DEV SET)
DST_DATA=my_data/dev_dst.json
python $BDIR/gpt2-dst.py --hyp_dir hyps/ex4/dev \
    --test_data $DST_DATA --args $DST_ARGS --checkpoint $CHECKPOINT -vv >> $LOG 2> $ERR

echo "Time: `date`" >> $LOG

# decode the test set (NEW TEST SET)
DST_DATA=my_data/test_dst.json
python $BDIR/gpt2-dst.py --hyp_dir hyps/ex4/test \
    --test_data $DST_DATA --args $DST_ARGS --checkpoint $CHECKPOINT -vv >> $LOG 2> $ERR

echo "Time: `date`" >> $LOG

