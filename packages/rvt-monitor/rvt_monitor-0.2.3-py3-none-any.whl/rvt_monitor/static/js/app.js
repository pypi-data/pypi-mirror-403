/**
 * RVT-Monitor Frontend Application
 */

// State
let ws = null;
let clientId = null;
let connected = false;
let devices = [];
let currentDeviceType = null;
let currentProfileId = null;

// DOM Elements
const elements = {
  connectionStatus: document.getElementById('connection-status'),
  deviceName: document.getElementById('device-name'),
  deviceManufacturer: document.getElementById('device-manufacturer'),
  deviceModel: document.getElementById('device-model'),
  deviceSerial: document.getElementById('device-serial'),
  deviceProtocol: document.getElementById('device-protocol'),
  deviceHardware: document.getElementById('device-hardware'),
  deviceFirmware: document.getElementById('device-firmware'),
  // Status cards
  ceilyStatusCard: document.getElementById('ceily-status-card'),
  wallyStatusCard: document.getElementById('wally-status-card'),
  // Dimension card
  dimensionCard: document.getElementById('dimension-card'),
  btnReadDimensions: document.getElementById('btn-read-dimensions'),
  btnSaveDimensions: document.getElementById('btn-save-dimensions'),
  dimensionTbody: document.getElementById('dimension-tbody'),
  // WiFi card
  wifiCard: document.getElementById('wifi-card'),
  btnReadWifi: document.getElementById('btn-read-wifi'),
  btnSetWifi: document.getElementById('btn-set-wifi'),
  wifiCurrentSsid: document.getElementById('wifi-current-ssid'),
  wifiStatus: document.getElementById('wifi-status'),
  wifiSsidInput: document.getElementById('wifi-ssid'),
  wifiPasswordInput: document.getElementById('wifi-password'),
  // Controls
  deviceSelect: document.getElementById('device-select'),
  btnScan: document.getElementById('btn-scan'),
  btnConnect: document.getElementById('btn-connect'),
  btnUp: document.getElementById('btn-up'),
  btnDown: document.getElementById('btn-down'),
  btnStop: document.getElementById('btn-stop'),
  logContainer: document.getElementById('log-container'),
  // Ceily elements
  ceily: {
    motionState: document.getElementById('ceily-motion-state'),
    mcuTemp: document.getElementById('ceily-mcu-temp'),
    // p2-only
    speedControlState: document.getElementById('ceily-speed-control-state'),
    motionPhase: document.getElementById('ceily-motion-phase'),
    position: document.getElementById('ceily-position'),
    positionPct: document.getElementById('ceily-position-pct'),
    remainDistance: document.getElementById('ceily-remain-distance'),
    currentVelocity: document.getElementById('ceily-current-velocity'),
    commandVelocity: document.getElementById('ceily-command-velocity'),
    torque: document.getElementById('ceily-torque'),
    positionVerified: document.getElementById('ceily-position-verified'),
    modelLearning: document.getElementById('ceily-model-learning'),
    limitSwitch: document.getElementById('ceily-limit-switch'),
    // p1-only
    limitSwitchP1: document.getElementById('ceily-limit-switch-p1'),
    positionP1: document.getElementById('ceily-position-p1'),
    velocityP1: document.getElementById('ceily-velocity-p1'),
    torqueP1: document.getElementById('ceily-torque-p1'),
    currentP1: document.getElementById('ceily-current-p1'),
    voltageP1: document.getElementById('ceily-voltage-p1'),
    temperatureP1: document.getElementById('ceily-temperature-p1'),
    // Motor (p2-only)
    servoConnected: document.getElementById('ceily-servo-connected'),
    servoEnabled: document.getElementById('ceily-servo-enabled'),
    alarm: document.getElementById('ceily-alarm'),
    rawVelocity: document.getElementById('ceily-raw-velocity'),
    rawTorque: document.getElementById('ceily-raw-torque'),
    current: document.getElementById('ceily-current'),
    voltage: document.getElementById('ceily-voltage'),
    temperature: document.getElementById('ceily-temperature'),
    tofFrontState: document.getElementById('ceily-tof-front-state'),
    tofFrontObject: document.getElementById('ceily-tof-front-object'),
    tofLeftState: document.getElementById('ceily-tof-left-state'),
    tofLeftObject: document.getElementById('ceily-tof-left-object'),
    tofRightState: document.getElementById('ceily-tof-right-state'),
    tofRightObject: document.getElementById('ceily-tof-right-object'),
  },
  // Wally elements
  wally: {
    motionState: document.getElementById('wally-motion-state'),
    mcuTemp: document.getElementById('wally-mcu-temp'),
    // p2-only
    speedControlState: document.getElementById('wally-speed-control-state'),
    motionPhase: document.getElementById('wally-motion-phase'),
    positionMm: document.getElementById('wally-position-mm'),
    positionPct: document.getElementById('wally-position-pct'),
    remainDistance: document.getElementById('wally-remain-distance'),
    currentVelocity: document.getElementById('wally-current-velocity'),
    commandVelocity: document.getElementById('wally-command-velocity'),
    torque: document.getElementById('wally-torque'),
    positionVerified: document.getElementById('wally-position-verified'),
    modelLearning: document.getElementById('wally-model-learning'),
    limitSwitch: document.getElementById('wally-limit-switch'),
    photoSensor: document.getElementById('wally-photo-sensor'),
    // p1-only
    limitSwitchP1: document.getElementById('wally-limit-switch-p1'),
    mlAlarmP1: document.getElementById('wally-ml-alarm-p1'),
    mrAlarmP1: document.getElementById('wally-mr-alarm-p1'),
    // Kinematics
    x: document.getElementById('wally-x'),
    y: document.getElementById('wally-y'),
    distance: document.getElementById('wally-distance'),
    angle: document.getElementById('wally-angle'),
    // Left motor (p2-only for connected)
    mlConnected: document.getElementById('wally-ml-connected'),
    mlEnabled: document.getElementById('wally-ml-enabled'),
    mlAlarm: document.getElementById('wally-ml-alarm'),
    mlVelocity: document.getElementById('wally-ml-velocity'),
    mlTorque: document.getElementById('wally-ml-torque'),
    mlCurrent: document.getElementById('wally-ml-current'),
    mlVoltage: document.getElementById('wally-ml-voltage'),
    mlTemperature: document.getElementById('wally-ml-temperature'),
    // Right motor (p2-only for connected)
    mrConnected: document.getElementById('wally-mr-connected'),
    mrEnabled: document.getElementById('wally-mr-enabled'),
    mrAlarm: document.getElementById('wally-mr-alarm'),
    mrVelocity: document.getElementById('wally-mr-velocity'),
    mrTorque: document.getElementById('wally-mr-torque'),
    mrCurrent: document.getElementById('wally-mr-current'),
    mrVoltage: document.getElementById('wally-mr-voltage'),
    mrTemperature: document.getElementById('wally-mr-temperature'),
    // ToF
    tofLeftStatus: document.getElementById('wally-tof-left-status'),
    tofLeftDist: document.getElementById('wally-tof-left-dist'),
    tofRightStatus: document.getElementById('wally-tof-right-status'),
    tofRightDist: document.getElementById('wally-tof-right-dist'),
  },
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  initWebSocket();
  initEventListeners();
  appendLog('INFO', 'RVT-Monitor started');
});

// WebSocket
function initWebSocket() {
  ws = new WebSocket(`ws://${location.host}/ws`);

  ws.onopen = () => {
    appendLog('INFO', 'WebSocket connected');
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    handleMessage(msg);
  };

  ws.onclose = () => {
    appendLog('WARNING', 'WebSocket disconnected, reconnecting...');
    clientId = null;
    setTimeout(initWebSocket, 3000);
  };

  ws.onerror = (error) => {
    appendLog('ERROR', 'WebSocket error');
  };
}

function sendWs(type, data = {}) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type, data }));
  }
}

function handleMessage(msg) {
  switch (msg.type) {
    case 'init':
      clientId = msg.data.client_id;
      if (msg.data.app_state) {
        updateAppState(msg.data.app_state);
      }
      // Restore cached device list on init
      if (msg.data.devices && msg.data.devices.length > 0) {
        updateDeviceList(msg.data.devices);
      }
      appendLog('INFO', `Client ID: ${clientId}`);
      break;

    case 'status':
      updateStatus(msg.data);
      break;

    case 'log':
      appendLog(msg.data.level, msg.data.message);
      break;

    case 'scan_result':
      updateDeviceList(msg.data, true);
      break;

    case 'error':
      appendLog('ERROR', msg.data.message);
      break;

    case 'command_result':
      if (!msg.data.success) {
        appendLog('ERROR', `Command failed: ${msg.data.action}`);
      }
      break;

    case 'dimensions':
      if (msg.data) {
        renderDimensionTable(msg.data);
      }
      break;

    case 'dimension_write_result':
      if (msg.data.success) {
        appendLog('INFO', `Dimension ${msg.data.id} set to ${msg.data.value}`);
      }
      break;

    case 'dimensions_save_result':
      if (msg.data.success) {
        appendLog('INFO', 'Dimensions saved to flash');
      }
      break;

    case 'wifi_status':
      if (msg.data) {
        updateWifiStatus(msg.data);
      }
      break;

    case 'wifi_set_result':
      if (msg.data.success) {
        elements.wifiSsidInput.value = '';
        elements.wifiPasswordInput.value = '';
        // Refresh WiFi status
        setTimeout(() => sendWs('read_wifi_status'), 2000);
      }
      break;
  }
}

// Event Listeners
function initEventListeners() {
  elements.btnScan.addEventListener('click', scanDevices);
  elements.btnConnect.addEventListener('click', toggleConnection);
  elements.btnUp.addEventListener('click', () => sendCommand('up'));
  elements.btnDown.addEventListener('click', () => sendCommand('down'));
  elements.btnStop.addEventListener('click', () => sendCommand('stop'));

  elements.deviceSelect.addEventListener('change', () => {
    elements.btnConnect.disabled = !elements.deviceSelect.value;
  });

  // Dimension buttons
  elements.btnReadDimensions.addEventListener('click', () => {
    sendWs('read_dimensions');
  });
  elements.btnSaveDimensions.addEventListener('click', () => {
    sendWs('save_dimensions');
  });

  // WiFi buttons
  elements.btnReadWifi.addEventListener('click', () => {
    sendWs('read_wifi_status');
  });
  elements.btnSetWifi.addEventListener('click', () => {
    const ssid = elements.wifiSsidInput.value.trim();
    const password = elements.wifiPasswordInput.value;
    if (ssid) {
      sendWs('set_wifi', { ssid, password });
    } else {
      appendLog('ERROR', 'SSID is required');
    }
  });
}

// Scan via WebSocket
function scanDevices() {
  elements.btnScan.disabled = true;
  elements.btnScan.textContent = 'Scanning...';
  sendWs('scan');

  setTimeout(() => {
    elements.btnScan.disabled = false;
    elements.btnScan.textContent = 'Scan';
  }, 10000);
}

// Connect/Disconnect via WebSocket
function toggleConnection() {
  if (connected) {
    sendWs('disconnect');
  } else {
    const address = elements.deviceSelect.value;
    const option = elements.deviceSelect.selectedOptions[0];
    const name = option ? option.textContent.split(' (')[0] : '';

    if (!address) return;

    setConnectionStatus('connecting');
    sendWs('connect', { address, name });
  }
}

// Commands via WebSocket
function sendCommand(action) {
  sendWs('command', { action });
}

// UI Updates
function updateAppState(state) {
  // App state handling (reserved for future use)
}

function setConnectionStatus(status) {
  const textMap = {
    connected: 'Connected',
    disconnected: 'Disconnected',
    connecting: 'Connecting...',
  };
  elements.connectionStatus.textContent = textMap[status] || status;
  elements.connectionStatus.className = `status-text ${status}`;

  connected = status === 'connected';
  elements.btnConnect.textContent = connected ? 'Disconnect' : 'Connect';

  if (!connected) {
    currentDeviceType = null;
    currentProfileId = null;
    // Clear device info
    elements.deviceName.textContent = '-';
    elements.deviceManufacturer.textContent = '-';
    elements.deviceModel.textContent = '-';
    elements.deviceSerial.textContent = '-';
    elements.deviceProtocol.textContent = '-';
    elements.deviceHardware.textContent = '-';
    elements.deviceFirmware.textContent = '-';
  }

  updateStatusCardVisibility();
  updateControlButtons();
}

function updateControlButtons() {
  elements.btnUp.disabled = !connected;
  elements.btnDown.disabled = !connected;
  elements.btnStop.disabled = !connected;
  elements.btnConnect.disabled = !elements.deviceSelect.value && !connected;
}

function updateStatus(data) {
  if (data.app_state) {
    updateAppState(data.app_state);
  }

  if (data.device_name) {
    elements.deviceName.textContent = data.device_name;
  }

  // Update profile ID and UI
  if (data.profile_id && data.profile_id !== currentProfileId) {
    console.log(`[UI] Profile switch: ${currentProfileId} -> ${data.profile_id}`);
    currentProfileId = data.profile_id;
    updateProfileUI(currentProfileId);
  }

  // Update device info (BLE SIG 0x180A) - only for v1-p2+
  if (data.device_info) {
    elements.deviceManufacturer.textContent = data.device_info.manufacturer_name || '-';
    elements.deviceModel.textContent = data.device_info.model_number || '-';
    elements.deviceSerial.textContent = data.device_info.serial_number || '-';
    elements.deviceProtocol.textContent = data.device_info.protocol_version ? `v${data.device_info.protocol_version}` : '-';
    elements.deviceHardware.textContent = data.device_info.hardware_revision || '-';
    elements.deviceFirmware.textContent = data.device_info.firmware_revision || '-';
  } else if (currentProfileId === 'v1-p1') {
    // v1-p1: No device info available
    elements.deviceManufacturer.textContent = 'N/A';
    elements.deviceModel.textContent = 'N/A';
    elements.deviceSerial.textContent = 'N/A';
    elements.deviceProtocol.textContent = 'v1';
    elements.deviceHardware.textContent = 'N/A';
    elements.deviceFirmware.textContent = 'N/A';
  }

  // Update device type BEFORE connection status (for card visibility)
  if (data.device_type && data.device_type !== currentDeviceType) {
    currentDeviceType = data.device_type;
    updateDeviceTypeUI(data.device_type);
  }

  // Now update connection status (which uses currentDeviceType)
  if (data.connected !== undefined) {
    setConnectionStatus(data.connected ? 'connected' : 'disconnected');
  }

  if (data.status) {
    // Update device type from status if not already set
    if (data.status.device_type && !currentDeviceType) {
      currentDeviceType = data.status.device_type;
      updateDeviceTypeUI(data.status.device_type);
      updateStatusCardVisibility();
    }

    if (data.status.device_type === 'ceily') {
      updateCeilyStatus(data.status);
    } else if (data.status.device_type === 'wally') {
      updateWallyStatus(data.status);
    }
  }

}

function updateDeviceTypeUI(deviceType) {
  const isCeily = deviceType === 'ceily';
  elements.btnUp.textContent = isCeily ? 'UP' : 'OPEN';
  elements.btnDown.textContent = isCeily ? 'DOWN' : 'CLOSE';
}

function updateProfileUI(profileId) {
  const isP2 = profileId === 'v1-p2';
  // Show/hide p2-only and p1-only elements
  document.querySelectorAll('.p2-only').forEach(el => {
    el.style.display = isP2 ? '' : 'none';
  });
  document.querySelectorAll('.p1-only').forEach(el => {
    el.style.display = isP2 ? 'none' : '';
  });
}

function updateStatusCardVisibility() {
  if (connected && currentDeviceType === 'ceily') {
    elements.ceilyStatusCard.style.display = 'block';
    elements.wallyStatusCard.style.display = 'none';
    elements.dimensionCard.style.display = 'block';
    elements.wifiCard.style.display = 'block';
  } else if (connected && currentDeviceType === 'wally') {
    elements.ceilyStatusCard.style.display = 'none';
    elements.wallyStatusCard.style.display = 'block';
    elements.dimensionCard.style.display = 'block';
    elements.wifiCard.style.display = 'block';
  } else {
    elements.ceilyStatusCard.style.display = 'none';
    elements.wallyStatusCard.style.display = 'none';
    elements.dimensionCard.style.display = 'none';
    elements.wifiCard.style.display = 'none';
  }
}

function getMotionStateText(state, deviceType) {
  const ceilyStates = {
    'DOWN': 'Down',
    'UP': 'Up',
    'MOVING_DOWN': 'Moving Down',
    'MOVING_UP': 'Moving Up',
    'STOP': 'Stopped',
    'EMERGENCY': 'Emergency',
    'INIT': 'Init',
  };
  const wallyStates = {
    'DOWN': 'Closed',
    'UP': 'Opened',
    'MOVING_DOWN': 'Closing',
    'MOVING_UP': 'Opening',
    'STOP': 'Stopped',
    'EMERGENCY': 'Emergency',
    'INIT': 'Init',
  };
  const map = deviceType === 'ceily' ? ceilyStates : wallyStates;
  return map[state] || state || '-';
}

function formatVoltage(mv) {
  if (mv === undefined || mv === null) return '-';
  return mv > 100 ? (mv / 1000).toFixed(1) : mv;
}

function formatTemp(raw) {
  if (raw === undefined || raw === null) return '-';
  return raw > 1000 ? (raw / 10).toFixed(1) : raw;
}

function getSpeedControlStateName(state) {
  const names = {0: 'Stop', 1: 'Accel', 2: 'Constant', 3: 'Decel'};
  return names[state] ?? `Unknown(${state})`;
}

function getMotionPhaseName(phase, deviceType) {
  if (deviceType === 'wally') {
    const names = {0: 'Stop', 1: 'Y Correct', 2: 'Angle Correct', 3: 'In-Place Align'};
    return names[phase] ?? `Unknown(${phase})`;
  }
  return phase === 0 ? 'N/A' : `${phase}`;
}

function updateCeilyStatus(status) {
  const el = elements.ceily;
  const isP2 = currentProfileId === 'v1-p2';

  el.motionState.textContent = getMotionStateText(status.motion_state, 'ceily');
  el.mcuTemp.textContent = status.mcu_temp ?? '-';

  if (isP2) {
    // p2 Common fields
    el.speedControlState.textContent = getSpeedControlStateName(status.speed_control_state);
    el.motionPhase.textContent = getMotionPhaseName(status.motion_phase, 'ceily');
    el.position.textContent = status.position_mm ?? '-';
    el.positionPct.textContent = status.position_percentage ?? '-';
    el.remainDistance.textContent = status.remain_distance ?? '-';
    el.currentVelocity.textContent = status.current_velocity ?? '-';
    el.commandVelocity.textContent = status.command_velocity ?? '-';
    el.torque.textContent = status.torque ?? '-';
    el.positionVerified.textContent = status.is_position_verified ? 'Yes' : 'No';
    el.positionVerified.className = status.is_position_verified ? 'status-ok' : 'status-warn';
    el.modelLearning.textContent = status.is_current_model_learning ? 'Yes' : 'No';
    el.limitSwitch.textContent = formatLimitSwitch(status.top_limit, status.bottom_limit);
  } else {
    // p1 fields
    el.limitSwitchP1.textContent = formatLimitSwitch(status.top_limit, status.bottom_limit);
    el.positionP1.textContent = status.position_mm?.toFixed(1) ?? '-';
    el.velocityP1.textContent = status.velocity_mm?.toFixed(1) ?? '-';
    el.torqueP1.textContent = status.torque?.toFixed(2) ?? '-';
    // p1 motor values
    el.currentP1.textContent = status.motor_current ?? '-';
    el.voltageP1.textContent = formatVoltage(status.voltage);
    el.temperatureP1.textContent = formatTemp(status.temperature);
  }

  // Motor - servo status is common to both p1 and p2
  el.servoConnected.textContent = status.servo_connected ? 'OK' : 'N/A';
  el.servoConnected.className = status.servo_connected ? 'status-ok' : 'status-warn';
  el.servoEnabled.textContent = status.servo_enabled ? 'ON' : 'OFF';
  el.servoEnabled.className = status.servo_enabled ? 'status-ok' : 'status-warn';
  el.alarm.textContent = status.servo_current_alarm ? `Code ${status.servo_current_alarm}` : 'None';

  if (isP2) {
    // p2 motor raw values
    el.rawVelocity.textContent = status.raw_velocity ?? '-';
    el.rawTorque.textContent = status.raw_torque ?? '-';
    el.current.textContent = status.motor_current ?? '-';
    el.voltage.textContent = formatVoltage(status.voltage);
    el.temperature.textContent = formatTemp(status.temperature);
  }

  // ToF sensors (nested objects with state_name, error_name, object_detected)
  const tofFront = status.tof_front || {};
  const tofLeft = status.tof_left || {};
  const tofRight = status.tof_right || {};

  el.tofFrontState.textContent = formatTofState(tofFront);
  el.tofFrontObject.textContent = tofFront.object_detected ? 'Yes' : 'No';
  el.tofLeftState.textContent = formatTofState(tofLeft);
  el.tofLeftObject.textContent = tofLeft.object_detected ? 'Yes' : 'No';
  el.tofRightState.textContent = formatTofState(tofRight);
  el.tofRightObject.textContent = tofRight.object_detected ? 'Yes' : 'No';
}

function formatTofState(tof) {
  if (!tof || tof.state_name === undefined) return '-';
  // Show disabled state
  if (tof.enable === false) {
    return 'Disabled';
  }
  if (tof.error_code === 0) {
    return tof.state_name;
  }
  return `${tof.state_name} (${tof.error_name})`;
}

function formatLimitSwitch(top, bottom) {
  const parts = [];
  if (top) parts.push('Top');
  if (bottom) parts.push('Bottom');
  return parts.length > 0 ? parts.join(', ') : 'None';
}

function formatWallyLimitSwitch(state) {
  if (state === undefined || state === null) return '-';
  // bit 0: closed, bit 1: opened
  const parts = [];
  if (state & 0x01) parts.push('Closed');
  if (state & 0x02) parts.push('Opened');
  return parts.length > 0 ? parts.join(', ') : 'None';
}

function updateWallyStatus(status) {
  const el = elements.wally;
  const isP2 = currentProfileId === 'v1-p2';

  el.motionState.textContent = getMotionStateText(status.motion_state, 'wally');
  el.mcuTemp.textContent = status.mcu_temp ?? '-';

  if (isP2) {
    // p2 Common fields
    el.speedControlState.textContent = getSpeedControlStateName(status.speed_control_state);
    el.motionPhase.textContent = getMotionPhaseName(status.motion_phase, 'wally');
    el.positionMm.textContent = status.position_mm ?? '-';
    el.positionPct.textContent = status.position_percentage ?? '-';
    el.remainDistance.textContent = status.remain_distance ?? '-';
    el.currentVelocity.textContent = status.current_velocity ?? '-';
    el.commandVelocity.textContent = status.command_velocity ?? '-';
    el.torque.textContent = status.torque ?? '-';
    el.positionVerified.textContent = status.is_position_verified ? 'Yes' : 'No';
    el.positionVerified.className = status.is_position_verified ? 'status-ok' : 'status-warn';
    el.modelLearning.textContent = status.is_current_model_learning ? 'Yes' : 'No';
    el.limitSwitch.textContent = formatWallyLimitSwitch(status.limit_switch_state);
    el.photoSensor.textContent = status.photo_sensor_state ?? '-';
  } else {
    // p1 fields
    el.limitSwitchP1.textContent = formatWallyLimitSwitch(status.limit_switch_state);
  }

  // Kinematics
  el.x.textContent = status.wally_x?.toFixed(1) ?? '-';
  el.y.textContent = status.wally_y?.toFixed(1) ?? '-';
  el.distance.textContent = status.distance_to_wall ?? '-';
  el.angle.textContent = status.angle?.toFixed(2) ?? '-';

  // Left motor
  const ml = status.motor_left || {};
  if (isP2) {
    el.mlConnected.textContent = ml.is_connected ? 'OK' : 'N/A';
    el.mlConnected.className = ml.is_connected ? 'status-ok' : 'status-warn';
    el.mlEnabled.textContent = ml.is_enabled ? 'ON' : 'OFF';
    el.mlEnabled.className = ml.is_enabled ? 'status-ok' : 'status-warn';
    el.mlAlarm.textContent = ml.current_alarm ? `Code ${ml.current_alarm}` : 'None';
    el.mlVelocity.textContent = ml.raw_velocity ?? '-';
    el.mlTorque.textContent = ml.raw_torque ?? '-';
  } else {
    el.mlAlarmP1.textContent = ml.current_alarm ? `Code ${ml.current_alarm}` : 'None';
    el.mlVelocity.textContent = ml.velocity?.toFixed(1) ?? '-';
    el.mlTorque.textContent = ml.torque?.toFixed(2) ?? '-';
  }
  el.mlCurrent.textContent = ml.current ?? '-';
  el.mlVoltage.textContent = formatVoltage(ml.voltage);
  el.mlTemperature.textContent = formatTemp(ml.temperature);

  // Right motor
  const mr = status.motor_right || {};
  if (isP2) {
    el.mrConnected.textContent = mr.is_connected ? 'OK' : 'N/A';
    el.mrConnected.className = mr.is_connected ? 'status-ok' : 'status-warn';
    el.mrEnabled.textContent = mr.is_enabled ? 'ON' : 'OFF';
    el.mrEnabled.className = mr.is_enabled ? 'status-ok' : 'status-warn';
    el.mrAlarm.textContent = mr.current_alarm ? `Code ${mr.current_alarm}` : 'None';
    el.mrVelocity.textContent = mr.raw_velocity ?? '-';
    el.mrTorque.textContent = mr.raw_torque ?? '-';
  } else {
    el.mrAlarmP1.textContent = mr.current_alarm ? `Code ${mr.current_alarm}` : 'None';
    el.mrVelocity.textContent = mr.velocity?.toFixed(1) ?? '-';
    el.mrTorque.textContent = mr.torque?.toFixed(2) ?? '-';
  }
  el.mrCurrent.textContent = mr.current ?? '-';
  el.mrVoltage.textContent = formatVoltage(mr.voltage);
  el.mrTemperature.textContent = formatTemp(mr.temperature);

  // ToF sensors (nested objects with state_name, error_name, distance)
  const tofLeft = status.tof_left || {};
  const tofRight = status.tof_right || {};

  el.tofLeftStatus.textContent = formatTofState(tofLeft);
  el.tofLeftDist.textContent = tofLeft.distance_mm?.toFixed(1) ?? '-';
  el.tofRightStatus.textContent = formatTofState(tofRight);
  el.tofRightDist.textContent = tofRight.distance_mm?.toFixed(1) ?? '-';
}

function updateDeviceList(deviceList, showLog = false) {
  devices = deviceList;
  elements.deviceSelect.innerHTML = '<option value="">Select a device</option>';

  deviceList.forEach(device => {
    const option = document.createElement('option');
    option.value = device.address;
    option.textContent = `${device.name} (${device.rssi} dBm)`;
    elements.deviceSelect.appendChild(option);
  });

  elements.deviceSelect.disabled = deviceList.length === 0;
  elements.btnScan.disabled = false;
  elements.btnScan.textContent = 'Scan';

  if (showLog) {
    appendLog('INFO', `${deviceList.length} device(s) found`);
  }
}

function appendLog(level, message) {
  const line = document.createElement('div');
  line.className = `log-line ${level.toLowerCase()}`;
  line.textContent = `[${formatTime(new Date())}] ${level}: ${message}`;
  elements.logContainer.appendChild(line);
  elements.logContainer.scrollTop = elements.logContainer.scrollHeight;

  while (elements.logContainer.children.length > 100) {
    elements.logContainer.removeChild(elements.logContainer.firstChild);
  }
}

function formatTime(date) {
  if (typeof date === 'string') {
    date = new Date(date);
  }
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}

// Dimension Table
function renderDimensionTable(data) {
  if (!data || !data.dimensions) {
    elements.dimensionTbody.innerHTML = '<tr><td colspan="3">No dimension data</td></tr>';
    return;
  }

  elements.dimensionTbody.innerHTML = '';
  data.dimensions.forEach(dim => {
    const tr = document.createElement('tr');

    // Name
    const tdName = document.createElement('td');
    tdName.textContent = dim.name;
    tr.appendChild(tdName);

    // Value (editable input)
    const tdValue = document.createElement('td');
    const input = document.createElement('input');
    input.type = 'number';
    input.value = dim.value;
    input.dataset.dimId = dim.id;
    input.dataset.originalValue = dim.value;
    // Auto-apply on blur if value changed
    input.addEventListener('blur', () => {
      const newValue = parseInt(input.value, 10);
      const originalValue = parseInt(input.dataset.originalValue, 10);
      if (!isNaN(newValue) && newValue !== originalValue) {
        sendWs('write_dimension', { id: dim.id, value: newValue });
        input.dataset.originalValue = newValue;
      }
    });
    tdValue.appendChild(input);
    tr.appendChild(tdValue);

    // Unit
    const tdUnit = document.createElement('td');
    tdUnit.textContent = dim.unit || '-';
    tr.appendChild(tdUnit);

    elements.dimensionTbody.appendChild(tr);
  });
}

// WiFi Status
function updateWifiStatus(data) {
  elements.wifiCurrentSsid.textContent = data.ssid || '-';
  if (data.connected) {
    elements.wifiStatus.textContent = 'Connected';
    elements.wifiStatus.className = 'status-text connected';
  } else {
    elements.wifiStatus.textContent = 'Disconnected';
    elements.wifiStatus.className = 'status-text disconnected';
  }
}
