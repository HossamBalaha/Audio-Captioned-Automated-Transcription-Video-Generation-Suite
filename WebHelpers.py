'''
========================================================================
        ╦ ╦┌─┐┌─┐┌─┐┌─┐┌┬┐  ╔╦╗┌─┐┌─┐┌┬┐┬ ┬  ╔╗ ┌─┐┬  ┌─┐┬ ┬┌─┐
        ╠═╣│ │└─┐└─┐├─┤│││  ║║║├─┤│ ┬ ││└┬┘  ╠╩╗├─┤│  ├─┤├─┤├─┤
        ╩ ╩└─┘└─┘└─┘┴ ┴┴ ┴  ╩ ╩┴ ┴└─┘─┴┘ ┴   ╚═╝┴ ┴┴─┘┴ ┴┴ ┴┴ ┴
========================================================================
# Author: Hossam Magdy Balaha
# Permissions and Citation: Refer to the README file.
'''

import threading, time, logging

# Use module logger so messages go through Python's logging system and appear with Flask output.
logger = logging.getLogger(__name__)


class JobStatusHistory(object):
  """Class to maintain a history of job statuses with timestamps."""

  def __init__(self):
    self.history = {}

  def addStatus(self, jobId, status):
    """Add a status entry for a job."""
    self.history[jobId] = status

  def getHistory(self, jobId):
    """Retrieve the status history for a specific job."""
    return self.history.get(jobId, [])

  def keys(self):
    return self.history.keys()

  def items(self):
    return self.history.items()

  def values(self):
    return self.history.values()

  def get(self, jobId, default=None):
    return self.history.get(jobId, default)

  def delete(self, jobId):
    if (jobId in self.history):
      del self.history[jobId]

  def clear(self):
    self.history.clear()

  def updateStatus(self, jobId, status):
    """Update the status of a job."""
    self.history[jobId] = status

  def __len__(self):
    return len(self.history)


class QueueWatcher(threading.Thread):
  """A thread to monitor the job queue and process jobs as they are added."""

  def __init__(self, func, maxJobs=1, maxTimeout=10):
    super().__init__()
    self.maxJobs = maxJobs
    self.func = func
    self.jobHistoryObj = JobStatusHistory()
    self.running = True
    self.daemon = False
    self.timout = maxTimeout
    self.counter = 0  # Counter to track the number of jobs processed.

  def run(self):
    """Continuously check the job queue and process jobs if available."""
    while (self.running):
      noOfBeingProcessedJobs = len(
        [status for status in self.jobHistoryObj.values() if (status == "processing")]
      )
      isBusy = noOfBeingProcessedJobs >= self.maxJobs

      if (not isBusy):
        logger.info(f"QueueWatcher: Processing jobs. Currently {noOfBeingProcessedJobs} jobs being processed.")
        if (not self.running):
          logger.info("QueueWatcher: Stopping thread as requested.")
          break

        # Process the next job if available
        for jobId, status in self.jobHistoryObj.items():
          if (status == "queued"):
            logger.info(f"QueueWatcher: Processing job {jobId}.")
            self.func(jobId)
            break

      # Sleep for a short duration before checking again.
      time.sleep(1)
      self.counter += 1
      if (self.counter >= self.timout):
        logger.info("QueueWatcher: No jobs to process. Sleeping for a while...")
        break

    logger.info("QueueWatcher: Exiting run loop.")
