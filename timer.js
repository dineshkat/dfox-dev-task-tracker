// Live Stopwatch & Time Tracker Helper
const TaskTimer = {
  seconds: 0,
  intervalId: null,
  isRunning: false,
  activeTaskId: null,
  activeTaskTitle: null,

  init() {
    this.restoreState();
    this.updateDisplay();
  },

  start(taskId = null, taskTitle = null) {
    if (this.isRunning) return;
    if (taskId) {
      this.activeTaskId = taskId;
      this.activeTaskTitle = taskTitle;
    }
    this.isRunning = true;
    this.intervalId = setInterval(() => {
      this.seconds++;
      this.updateDisplay();
      this.saveState();
    }, 1000);
    this.saveState();
    this.updateUIState();
  },

  pause() {
    if (!this.isRunning) return;
    clearInterval(this.intervalId);
    this.isRunning = false;
    this.saveState();
    this.updateUIState();
  },

  reset() {
    this.pause();
    this.seconds = 0;
    this.activeTaskId = null;
    this.activeTaskTitle = null;
    this.saveState();
    this.updateDisplay();
    this.updateUIState();
  },

  formatTime(totalSecs) {
    const h = Math.floor(totalSecs / 3600);
    const m = Math.floor((totalSecs % 3600) / 60);
    const s = totalSecs % 60;
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  },

  getHoursAndMinutes() {
    const hours = Math.floor(this.seconds / 3600);
    const minutes = Math.floor((this.seconds % 3600) / 60);
    return { hours, minutes };
  },

  updateDisplay() {
    const displayEl = document.getElementById('active-stopwatch-display');
    if (displayEl) {
      displayEl.textContent = this.formatTime(this.seconds);
    }
  },

  updateUIState() {
    const startBtn = document.getElementById('btn-timer-start');
    const pauseBtn = document.getElementById('btn-timer-pause');
    const activeTaskLabel = document.getElementById('active-timer-task-label');

    if (startBtn && pauseBtn) {
      if (this.isRunning) {
        startBtn.style.display = 'none';
        pauseBtn.style.display = 'inline-flex';
      } else {
        startBtn.style.display = 'inline-flex';
        pauseBtn.style.display = 'none';
      }
    }

    if (activeTaskLabel) {
      activeTaskLabel.textContent = this.activeTaskTitle 
        ? `Tracking: ${this.activeTaskTitle}` 
        : 'General Development Time';
    }
  },

  saveState() {
    try {
      localStorage.setItem('dfox_timer', JSON.stringify({
        seconds: this.seconds,
        isRunning: this.isRunning,
        activeTaskId: this.activeTaskId,
        activeTaskTitle: this.activeTaskTitle,
        lastTimestamp: Date.now()
      }));
    } catch(e) {}
  },

  restoreState() {
    try {
      const saved = localStorage.getItem('dfox_timer');
      if (saved) {
        const data = JSON.parse(saved);
        this.seconds = data.seconds || 0;
        this.activeTaskId = data.activeTaskId;
        this.activeTaskTitle = data.activeTaskTitle;
        if (data.isRunning && data.lastTimestamp) {
          const elapsed = Math.floor((Date.now() - data.lastTimestamp) / 1000);
          this.seconds += elapsed;
          this.start();
        }
      }
    } catch(e) {}
  }
};
