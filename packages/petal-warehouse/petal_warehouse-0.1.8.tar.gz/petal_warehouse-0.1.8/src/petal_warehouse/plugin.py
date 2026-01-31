from . import __version__, logger

from petal_app_manager.plugins.base import Petal
from petal_app_manager.plugins.decorators import http_action, websocket_action
from petal_app_manager.proxies.redis import RedisProxy
from petal_app_manager.proxies.localdb import LocalDBProxy
from petal_app_manager.proxies.external import MavLinkExternalProxy

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from pymavlink import mavutil
from pymavlink.dialects.v20 import all as dialects_v20
from pymavlink.dialects.v10 import all as dialects_v10
from pymavlink.quaternion import QuaternionBase

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Union, List

from datetime import datetime
from pathlib import Path

import threading
import json, math

from fastapi import HTTPException

import asyncio

import time
# this version uses websockets
websocket_clients_pos_update = set()

websocket_clients_target_traj_update = set()

class PetalWarehouse(Petal):
    name = "petal-warehouse"
    version = __version__

    def startup(self):
        super().startup()
        self.mavlink_proxy = self._proxies.get("ext_mavlink")

        try:
            logger.info("Initializing Blender Realtime Client...")
            self.blender_client = BlenderRealtimeClient(mav_proxy=self.mavlink_proxy)
            logger.info("Blender Realtime Client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Blender Realtime Client: {e}")
            self.blender_client = None
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize Blender Realtime Client: {e}"
            )
    
    def shutdown(self):
        """Shutdown method to clean up resources"""
        if hasattr(self, 'blender_client'):
            logger.info("Stopping Blender Realtime Client...")
            self.blender_client.stop()
            self.blender_client = None
            
        super().shutdown()

    # WebSocket endpoint for position updates
    @websocket_action(
        path="/ws/local_position"
    )
    async def local_position_websocket(self, websocket: WebSocket):
        await websocket.accept()
        websocket_clients_pos_update.add(websocket)
        try:
            while True:
                await websocket.receive_text()  # Keep the connection alive
        except WebSocketDisconnect:
            websocket_clients_pos_update.discard(websocket)

    # WebSocket endpoint for trajectory target updates
    @websocket_action(
        path="/ws/trajectory_target"
    )
    async def target_traj_websocket(self, websocket: WebSocket):
        await websocket.accept()
        websocket_clients_target_traj_update.add(websocket)
        try:
            while True:
                await websocket.receive_text()  # Keep the connection alive
        except WebSocketDisconnect:
            websocket_clients_target_traj_update.discard(websocket)


class BlenderRealtimeClient:
    def __init__(self, mav_proxy: MavLinkExternalProxy):
        
        # MAVLink setup
        self.mav_proxy = mav_proxy

        # Store latest position and attitude data
        self.latest_position = {"x": 0, "y": 0, "z": 0, "timestamp": time.time()}
        self.latest_yaw = {"yaw": 0, "timestamp": time.time()}
        self.latest_target_traj = {"x": 0, "y": 0, "z": 0,"yaw": 0, "timestamp": time.time()}

        def handler_pos(msg: mavutil.mavlink.MAVLink_message) -> bool:
            self.process_position_message(msg)
            return True

        def handler_att(msg: mavutil.mavlink.MAVLink_message) -> bool:
            self.process_attitude_message(msg)
            return True
        
        def handler_target_trajectory(msg: mavutil.mavlink.MAVLink_message) -> bool:
            self.process_target_trajectory_message(msg)
            return True
        
        self._handler_pos = handler_pos
        self._handler_att = handler_att
        self._handler_target_trajectory = handler_target_trajectory

        self.mav_proxy.register_handler(
            key=str(dialects_v20.MAVLINK_MSG_ID_LOCAL_POSITION_NED),
            fn=self._handler_pos
        )

        self.mav_proxy.register_handler(
            key=str(dialects_v20.MAVLINK_MSG_ID_ATTITUDE_QUATERNION),
            fn=self._handler_att
        )

        self.mav_proxy.register_handler(
            key=str(dialects_v20.MAVLINK_MSG_ID_LEAF_EXTERNAL_TRAJECTORY_SETPOINT_ENU),
            fn=self._handler_target_trajectory
        )
        
        self.receiving = True

        # Start sending thread (combines position + yaw and sends to Blender)
        self.send_thread = threading.Thread(target=self._send_loop, daemon=True, name="BlenderPositionSender")
        self.send_thread.start()

    def process_position_message(self, msg):
        """Process VEHICLE_LOCAL_POSITION message"""
        self.latest_position = {
            "x": msg.x,  # North position in meters
            "y": msg.y,  # East position in meters  
            "z": msg.z,  # Down position in meters (negative = up)
            "timestamp": time.time()
        }
        logger.debug(f"[MAVLink] Position: x={msg.x:.2f}, y={msg.y:.2f}, z={msg.z:.2f}")

    def process_attitude_message(self, msg):
        """Process VEHICLE_ATTITUDE message and extract yaw"""
        try:
            # Get quaternion from message
            q = [msg.q1, msg.q2, msg.q3, msg.q4] # (w, x, y, z)
            
            # Convert quaternion to Euler angles (roll, pitch, yaw in radians)
            roll, pitch, yaw = QuaternionBase(q).euler
            
            # Convert yaw to enu
            yaw_enu = -yaw + 1.5707963267948966  # Convert from NED to ENU (yaw in radians)
            
            self.latest_yaw = {
                "yaw": yaw_enu,
                "timestamp": time.time()
            }
            logger.debug(f"[MAVLink] Yaw: {yaw_enu:.2f}°")
                
        except Exception as e:
            logger.error(f"[MAVLink] Error processing attitude: {e}")

    def process_target_trajectory_message(self, msg):
        """Process TARGET_TRAJECTORY message (if needed)"""
        # This can be extended to handle trajectory messages if required
        try:
            # Example processing logic (if needed)
            self.latest_target_traj = { 
                "x": msg.x,  # North position in meters
                "y": msg.y,  # East position in meters  
                "z": msg.z,  # Down position in meters (negative = up)
                "yaw": msg.yaw,  # Yaw in radians
                "timestamp": time.time()
            }

        except Exception as e:
            logger.error(f"[MAVLink] Error processing target trajectory: {e}")

    def _send_loop(self):
        """Periodically send combined position + yaw to Blender via WebSocket"""
        logger.info("[Sender] Starting position sender to Blender...")
        while self.receiving:
            try:
                # Get latest data
                pos = self.latest_position.copy()
                yaw_data = self.latest_yaw.copy()

                self.send_position(     # Convert NED to ENU
                    pos["y"],           # East
                    pos["x"],           # North
                    -pos["z"],          # Up
                    yaw_data["yaw"] # Yaw in rad
                )

                target_traj = self.latest_target_traj.copy()

                self.send_target_traj(  # ENU
                    target_traj["x"],    # East
                    target_traj["y"],    # North
                    target_traj["z"],   # Up
                    target_traj["yaw"] # Yaw in rad
                )
                
            except Exception as e:
                logger.error(f"[Sender] Error sending to Blender: {e}")
            
            time.sleep(0.1)  # Send at 10Hz

    def send_position(self, x, y, z, yaw):
        """Send position to Blender via WebSocket"""
        msg = {
            "type": "position_update",
            "x": x,
            "y": y,
            "z": z,
            "yaw": yaw
        }
        try:
            for client in websocket_clients_pos_update:
                if client.client_state == WebSocketState.CONNECTED:
                    asyncio.run(client.send_text(json.dumps(msg)))
                    logger.debug(f"[WebSocket] Sent position to Blender: {msg}")
                else:
                    logger.debug("[WebSocket] Client not connected, skipping send")
        except Exception as e:
            logger.error(f"[WebSocket] Send error: {e}")

    def send_target_traj(self, x, y, z, yaw):
        """Send target traj to Blender via WebSocket"""
        msg = {
            "type": "target_trajectory_update",
            "x": x,
            "y": y,
            "z": z,
            "yaw": yaw
        }
        try:
            for client in websocket_clients_target_traj_update:
                if client.client_state == WebSocketState.CONNECTED:
                    asyncio.run(client.send_text(json.dumps(msg)))
                    logger.debug(f"[WebSocket] Sent position to Blender: {msg}")
                else:
                    logger.debug("[WebSocket] Client not connected, skipping send")
        except Exception as e:
            logger.error(f"[WebSocket] Send error: {e}")

    def stop(self):
        """Stop all operations"""
        logger.info("[System] Stopping MAVLink receiver...")
        self.receiving = False

        self.mav_proxy.unregister_handler(
            key=str(dialects_v20.MAVLINK_MSG_ID_LOCAL_POSITION_NED),
            fn=self._handler_pos
        )
        self.mav_proxy.unregister_handler(
            key=str(dialects_v20.MAVLINK_MSG_ID_ATTITUDE_QUATERNION),
            fn=self._handler_att
        )

        self.mav_proxy.unregister_handler(
            key=str(dialects_v20.MAVLINK_MSG_ID_LEAF_EXTERNAL_TRAJECTORY_SETPOINT_ENU),
            fn=self._handler_target_trajectory
        )
        logger.info("[System] MAVLink receiver stopped")
        