"""
Cache endpoint handlers for SignalPilot AI.
Provides REST API handlers for chat histories, app values, and checkpoints caching.
"""

import json
from typing import Any, Dict, Optional

from jupyter_server.base.handlers import APIHandler
import tornado

from .cache_service import get_cache_service, get_checkpoint_cache_manager, get_cell_state_cache_manager


class ChatHistoriesHandler(APIHandler):
    """Handler for chat histories cache operations"""
    
    @tornado.web.authenticated
    def get(self, chat_id=None):
        """Get chat histories or specific chat history"""
        try:
            cache_service = get_cache_service()
            
            if not cache_service.is_available():
                self.set_status(503)
                self.finish(json.dumps({
                    "error": "Cache service not available",
                    "message": "Persistent storage is not accessible"
                }))
                return
            
            if chat_id:
                # Get specific chat history
                history = cache_service.get_chat_history(chat_id)
                if history is None:
                    self.set_status(404)
                    self.finish(json.dumps({
                        "error": "Chat history not found",
                        "chat_id": chat_id
                    }))
                else:
                    self.finish(json.dumps({
                        "chat_id": chat_id,
                        "history": history
                    }))
            else:
                # Get all chat histories
                histories = cache_service.get_chat_histories()
                self.finish(json.dumps({
                    "chat_histories": histories,
                    "count": len(histories)
                }))
                
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))
    
    @tornado.web.authenticated
    def post(self, chat_id=None):
        """Create or update chat history"""
        try:
            cache_service = get_cache_service()
            
            if not cache_service.is_available():
                self.set_status(503)
                self.finish(json.dumps({
                    "error": "Cache service not available",
                    "message": "Persistent storage is not accessible"
                }))
                return
            
            # Parse request body
            try:
                body = json.loads(self.request.body.decode('utf-8'))
            except json.JSONDecodeError:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "Invalid JSON in request body"
                }))
                return
            
            if chat_id:
                # Update specific chat history
                history_data = body.get('history')
                if history_data is None:
                    self.set_status(400)
                    self.finish(json.dumps({
                        "error": "Missing 'history' field in request body"
                    }))
                    return
                
                success = cache_service.set_chat_history(chat_id, history_data)
                if success:
                    self.finish(json.dumps({
                        "success": True,
                        "chat_id": chat_id,
                        "message": "Chat history updated successfully"
                    }))
                else:
                    self.set_status(500)
                    self.finish(json.dumps({
                        "error": "Failed to save chat history"
                    }))
            else:
                # Bulk update operation
                chat_histories = body.get('chat_histories', {})
                if not isinstance(chat_histories, dict):
                    self.set_status(400)
                    self.finish(json.dumps({
                        "error": "'chat_histories' must be an object"
                    }))
                    return
                
                # Update each chat history
                failures = []
                successes = []
                
                for cid, history in chat_histories.items():
                    if cache_service.set_chat_history(cid, history):
                        successes.append(cid)
                    else:
                        failures.append(cid)
                
                self.finish(json.dumps({
                    "success": len(failures) == 0,
                    "updated": successes,
                    "failed": failures,
                    "message": f"Updated {len(successes)} chat histories, {len(failures)} failed"
                }))
                
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))
    
    @tornado.web.authenticated
    def delete(self, chat_id=None):
        """Delete chat history or all chat histories"""
        try:
            cache_service = get_cache_service()
            
            if not cache_service.is_available():
                self.set_status(503)
                self.finish(json.dumps({
                    "error": "Cache service not available",
                    "message": "Persistent storage is not accessible"
                }))
                return
            
            if chat_id:
                # Delete specific chat history
                success = cache_service.delete_chat_history(chat_id)
                if success:
                    self.finish(json.dumps({
                        "success": True,
                        "chat_id": chat_id,
                        "message": "Chat history deleted successfully"
                    }))
                else:
                    self.set_status(500)
                    self.finish(json.dumps({
                        "error": "Failed to delete chat history"
                    }))
            else:
                # Clear all chat histories
                success = cache_service.clear_chat_histories()
                if success:
                    self.finish(json.dumps({
                        "success": True,
                        "message": "All chat histories cleared successfully"
                    }))
                else:
                    self.set_status(500)
                    self.finish(json.dumps({
                        "error": "Failed to clear chat histories"
                    }))
                    
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))


class AppValuesHandler(APIHandler):
    """Handler for app values cache operations"""
    
    @tornado.web.authenticated
    def get(self, key=None):
        """Get app values or specific app value"""
        try:
            cache_service = get_cache_service()
            
            if not cache_service.is_available():
                self.set_status(503)
                self.finish(json.dumps({
                    "error": "Cache service not available",
                    "message": "Persistent storage is not accessible"
                }))
                return
            
            if key:
                # Get specific app value
                default = self.get_argument('default', None)
                try:
                    if default:
                        default = json.loads(default)
                except json.JSONDecodeError:
                    pass  # Use string default
                
                value = cache_service.get_app_value(key, default)
                self.finish(json.dumps({
                    "key": key,
                    "value": value
                }))
            else:
                # Get all app values
                values = cache_service.get_app_values()
                self.finish(json.dumps({
                    "app_values": values,
                    "count": len(values)
                }))
                
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))
    
    @tornado.web.authenticated
    def post(self, key=None):
        """Create or update app value"""
        try:
            cache_service = get_cache_service()
            
            if not cache_service.is_available():
                self.set_status(503)
                self.finish(json.dumps({
                    "error": "Cache service not available",
                    "message": "Persistent storage is not accessible"
                }))
                return
            
            # Parse request body
            try:
                body = json.loads(self.request.body.decode('utf-8'))
            except json.JSONDecodeError:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "Invalid JSON in request body"
                }))
                return
            
            if key:
                # Update specific app value
                value_data = body.get('value')
                if value_data is None:
                    self.set_status(400)
                    self.finish(json.dumps({
                        "error": "Missing 'value' field in request body"
                    }))
                    return
                
                success = cache_service.set_app_value(key, value_data)
                if success:
                    self.finish(json.dumps({
                        "success": True,
                        "key": key,
                        "message": "App value updated successfully"
                    }))
                else:
                    self.set_status(500)
                    self.finish(json.dumps({
                        "error": "Failed to save app value"
                    }))
            else:
                # Bulk update operation
                app_values = body.get('app_values', {})
                if not isinstance(app_values, dict):
                    self.set_status(400)
                    self.finish(json.dumps({
                        "error": "'app_values' must be an object"
                    }))
                    return
                
                # Update each app value
                failures = []
                successes = []
                
                for k, value in app_values.items():
                    if cache_service.set_app_value(k, value):
                        successes.append(k)
                    else:
                        failures.append(k)
                
                self.finish(json.dumps({
                    "success": len(failures) == 0,
                    "updated": successes,
                    "failed": failures,
                    "message": f"Updated {len(successes)} app values, {len(failures)} failed"
                }))
                
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))
    
    @tornado.web.authenticated
    def delete(self, key=None):
        """Delete app value or all app values"""
        try:
            cache_service = get_cache_service()
            
            if not cache_service.is_available():
                self.set_status(503)
                self.finish(json.dumps({
                    "error": "Cache service not available",
                    "message": "Persistent storage is not accessible"
                }))
                return
            
            if key:
                # Delete specific app value
                success = cache_service.delete_app_value(key)
                if success:
                    self.finish(json.dumps({
                        "success": True,
                        "key": key,
                        "message": "App value deleted successfully"
                    }))
                else:
                    self.set_status(500)
                    self.finish(json.dumps({
                        "error": "Failed to delete app value"
                    }))
            else:
                # Clear all app values
                success = cache_service.clear_app_values()
                if success:
                    self.finish(json.dumps({
                        "success": True,
                        "message": "All app values cleared successfully"
                    }))
                else:
                    self.set_status(500)
                    self.finish(json.dumps({
                        "error": "Failed to clear app values"
                    }))
                    
        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))


class CacheInfoHandler(APIHandler):
    """Handler for cache service information"""

    @tornado.web.authenticated
    def get(self):
        """Get cache service information and statistics"""
        try:
            cache_service = get_cache_service()
            info = cache_service.get_cache_info()
            self.finish(json.dumps(info))

        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))


class CheckpointHandler(APIHandler):
    """Handler for individual checkpoint operations"""

    @tornado.web.authenticated
    def get(self, notebook_id=None, checkpoint_id=None):
        """Get a specific checkpoint or list checkpoints for a notebook"""
        try:
            checkpoint_manager = get_checkpoint_cache_manager()

            if not checkpoint_manager.is_available():
                self.set_status(503)
                self.finish(json.dumps({
                    "error": "Checkpoint cache service not available",
                    "message": "Persistent storage is not accessible"
                }))
                return

            if notebook_id and checkpoint_id:
                # Get specific checkpoint
                checkpoint = checkpoint_manager.get_checkpoint(notebook_id, checkpoint_id)
                if checkpoint is None:
                    self.set_status(404)
                    self.finish(json.dumps({
                        "error": "Checkpoint not found",
                        "notebook_id": notebook_id,
                        "checkpoint_id": checkpoint_id
                    }))
                else:
                    self.finish(json.dumps({
                        "checkpoint": checkpoint
                    }))
            elif notebook_id:
                # List all checkpoints for a notebook
                checkpoints = checkpoint_manager.list_checkpoints(notebook_id)
                self.finish(json.dumps({
                    "notebook_id": notebook_id,
                    "checkpoints": checkpoints,
                    "count": len(checkpoints)
                }))
            else:
                # List all notebook IDs with checkpoints
                notebook_ids = checkpoint_manager.list_notebook_ids()
                self.finish(json.dumps({
                    "notebook_ids": notebook_ids,
                    "count": len(notebook_ids)
                }))

        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))

    @tornado.web.authenticated
    def post(self, notebook_id=None, checkpoint_id=None):
        """Create or update a checkpoint"""
        try:
            checkpoint_manager = get_checkpoint_cache_manager()

            if not checkpoint_manager.is_available():
                self.set_status(503)
                self.finish(json.dumps({
                    "error": "Checkpoint cache service not available",
                    "message": "Persistent storage is not accessible"
                }))
                return

            # Parse request body
            try:
                body = json.loads(self.request.body.decode('utf-8'))
            except json.JSONDecodeError:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "Invalid JSON in request body"
                }))
                return

            if notebook_id and checkpoint_id:
                # Create/update specific checkpoint
                checkpoint_data = body.get('checkpoint')
                if checkpoint_data is None:
                    self.set_status(400)
                    self.finish(json.dumps({
                        "error": "Missing 'checkpoint' field in request body"
                    }))
                    return

                success = checkpoint_manager.set_checkpoint(notebook_id, checkpoint_id, checkpoint_data)
                if success:
                    self.finish(json.dumps({
                        "success": True,
                        "notebook_id": notebook_id,
                        "checkpoint_id": checkpoint_id,
                        "message": "Checkpoint saved successfully"
                    }))
                else:
                    self.set_status(500)
                    self.finish(json.dumps({
                        "error": "Failed to save checkpoint"
                    }))
            else:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "Both notebook_id and checkpoint_id are required"
                }))

        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))

    @tornado.web.authenticated
    def delete(self, notebook_id=None, checkpoint_id=None):
        """Delete a checkpoint or all checkpoints for a notebook"""
        try:
            checkpoint_manager = get_checkpoint_cache_manager()

            if not checkpoint_manager.is_available():
                self.set_status(503)
                self.finish(json.dumps({
                    "error": "Checkpoint cache service not available",
                    "message": "Persistent storage is not accessible"
                }))
                return

            if notebook_id and checkpoint_id:
                # Delete specific checkpoint
                success = checkpoint_manager.delete_checkpoint(notebook_id, checkpoint_id)
                if success:
                    self.finish(json.dumps({
                        "success": True,
                        "notebook_id": notebook_id,
                        "checkpoint_id": checkpoint_id,
                        "message": "Checkpoint deleted successfully"
                    }))
                else:
                    self.set_status(500)
                    self.finish(json.dumps({
                        "error": "Failed to delete checkpoint"
                    }))
            elif notebook_id:
                # Delete all checkpoints for a notebook
                success = checkpoint_manager.clear_checkpoints_for_notebook(notebook_id)
                if success:
                    self.finish(json.dumps({
                        "success": True,
                        "notebook_id": notebook_id,
                        "message": "All checkpoints deleted for notebook"
                    }))
                else:
                    self.set_status(500)
                    self.finish(json.dumps({
                        "error": "Failed to delete checkpoints for notebook"
                    }))
            else:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "notebook_id is required"
                }))

        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))


class CheckpointClearAfterHandler(APIHandler):
    """Handler for clearing checkpoints after a specific checkpoint"""

    @tornado.web.authenticated
    def post(self, notebook_id=None):
        """Clear all checkpoints after a specific checkpoint"""
        try:
            checkpoint_manager = get_checkpoint_cache_manager()

            if not checkpoint_manager.is_available():
                self.set_status(503)
                self.finish(json.dumps({
                    "error": "Checkpoint cache service not available"
                }))
                return

            if not notebook_id:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "notebook_id is required"
                }))
                return

            # Parse request body
            try:
                body = json.loads(self.request.body.decode('utf-8'))
            except json.JSONDecodeError:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "Invalid JSON in request body"
                }))
                return

            checkpoint_id = body.get('checkpoint_id')
            if not checkpoint_id:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "Missing 'checkpoint_id' in request body"
                }))
                return

            success = checkpoint_manager.clear_checkpoints_after(notebook_id, checkpoint_id)
            if success:
                self.finish(json.dumps({
                    "success": True,
                    "notebook_id": notebook_id,
                    "checkpoint_id": checkpoint_id,
                    "message": "Checkpoints cleared after specified checkpoint"
                }))
            else:
                self.set_status(404)
                self.finish(json.dumps({
                    "error": "Checkpoint not found",
                    "checkpoint_id": checkpoint_id
                }))

        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))


class CheckpointMigrateHandler(APIHandler):
    """Handler for migrating checkpoints from old format"""

    @tornado.web.authenticated
    def post(self):
        """Import checkpoints from the old single-file format"""
        try:
            checkpoint_manager = get_checkpoint_cache_manager()
            cache_service = get_cache_service()

            if not checkpoint_manager.is_available():
                self.set_status(503)
                self.finish(json.dumps({
                    "error": "Checkpoint cache service not available"
                }))
                return

            # Get old checkpoints from app_values
            old_checkpoints = cache_service.get_app_value('notebookCheckpoints', {})

            if not old_checkpoints:
                self.finish(json.dumps({
                    "success": True,
                    "migrated": 0,
                    "message": "No checkpoints to migrate"
                }))
                return

            # Import to new format
            success = checkpoint_manager.import_checkpoints(old_checkpoints)

            if success:
                # Count what was migrated
                total_notebooks = len(old_checkpoints)
                total_checkpoints = sum(len(cps) for cps in old_checkpoints.values())

                # Clear old checkpoints from app_values
                cache_service.delete_app_value('notebookCheckpoints')

                self.finish(json.dumps({
                    "success": True,
                    "migrated_notebooks": total_notebooks,
                    "migrated_checkpoints": total_checkpoints,
                    "message": "Checkpoints migrated successfully"
                }))
            else:
                self.set_status(500)
                self.finish(json.dumps({
                    "error": "Failed to migrate checkpoints"
                }))

        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))


class CheckpointStatsHandler(APIHandler):
    """Handler for checkpoint cache statistics"""

    @tornado.web.authenticated
    def get(self):
        """Get checkpoint cache statistics"""
        try:
            checkpoint_manager = get_checkpoint_cache_manager()
            stats = checkpoint_manager.get_cache_stats()
            self.finish(json.dumps(stats))

        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))


class CellStateHandler(APIHandler):
    """Handler for notebook cell state operations"""

    @tornado.web.authenticated
    def get(self, notebook_id=None):
        """Get cell state for a notebook or list all notebook IDs"""
        try:
            cell_state_manager = get_cell_state_cache_manager()

            if not cell_state_manager.is_available():
                self.set_status(503)
                self.finish(json.dumps({
                    "error": "Cell state cache service not available",
                    "message": "Persistent storage is not accessible"
                }))
                return

            if notebook_id:
                # Get cell state for specific notebook
                cell_state = cell_state_manager.get_cell_state(notebook_id)
                if cell_state is None:
                    self.set_status(404)
                    self.finish(json.dumps({
                        "error": "Cell state not found",
                        "notebook_id": notebook_id
                    }))
                else:
                    self.finish(json.dumps({
                        "notebook_id": notebook_id,
                        "cell_state": cell_state
                    }))
            else:
                # List all notebook IDs with cell states
                notebook_ids = cell_state_manager.list_notebook_ids()
                self.finish(json.dumps({
                    "notebook_ids": notebook_ids,
                    "count": len(notebook_ids)
                }))

        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))

    @tornado.web.authenticated
    def post(self, notebook_id=None):
        """Create or update cell state for a notebook"""
        try:
            cell_state_manager = get_cell_state_cache_manager()

            if not cell_state_manager.is_available():
                self.set_status(503)
                self.finish(json.dumps({
                    "error": "Cell state cache service not available"
                }))
                return

            if not notebook_id:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "notebook_id is required"
                }))
                return

            # Parse request body
            try:
                body = json.loads(self.request.body.decode('utf-8'))
            except json.JSONDecodeError:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "Invalid JSON in request body"
                }))
                return

            cell_state_data = body.get('cell_state')
            if cell_state_data is None:
                self.set_status(400)
                self.finish(json.dumps({
                    "error": "Missing 'cell_state' field in request body"
                }))
                return

            success = cell_state_manager.set_cell_state(notebook_id, cell_state_data)
            if success:
                self.finish(json.dumps({
                    "success": True,
                    "notebook_id": notebook_id,
                    "message": "Cell state saved successfully"
                }))
            else:
                self.set_status(500)
                self.finish(json.dumps({
                    "error": "Failed to save cell state"
                }))

        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))

    @tornado.web.authenticated
    def delete(self, notebook_id=None):
        """Delete cell state for a notebook or all cell states"""
        try:
            cell_state_manager = get_cell_state_cache_manager()

            if not cell_state_manager.is_available():
                self.set_status(503)
                self.finish(json.dumps({
                    "error": "Cell state cache service not available"
                }))
                return

            if notebook_id:
                # Delete cell state for specific notebook
                success = cell_state_manager.delete_cell_state(notebook_id)
                if success:
                    self.finish(json.dumps({
                        "success": True,
                        "notebook_id": notebook_id,
                        "message": "Cell state deleted successfully"
                    }))
                else:
                    self.set_status(500)
                    self.finish(json.dumps({
                        "error": "Failed to delete cell state"
                    }))
            else:
                # Clear all cell states
                success = cell_state_manager.clear_all_cell_states()
                if success:
                    self.finish(json.dumps({
                        "success": True,
                        "message": "All cell states cleared successfully"
                    }))
                else:
                    self.set_status(500)
                    self.finish(json.dumps({
                        "error": "Failed to clear cell states"
                    }))

        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))


class CellStateMigrateHandler(APIHandler):
    """Handler for migrating cell states from old format"""

    @tornado.web.authenticated
    def post(self):
        """Migrate cell states from old app_values format"""
        try:
            cell_state_manager = get_cell_state_cache_manager()
            cache_service = get_cache_service()

            if not cell_state_manager.is_available():
                self.set_status(503)
                self.finish(json.dumps({
                    "error": "Cell state cache service not available"
                }))
                return

            # Get all app values to find cell states
            app_values = cache_service.get_app_values()

            # Migrate cell states
            result = cell_state_manager.migrate_from_app_values(app_values)

            if result["migrated"] > 0:
                # Remove migrated keys from app_values
                prefix = "notebook-cell-state:"
                for key in list(app_values.keys()):
                    if key.startswith(prefix):
                        cache_service.delete_app_value(key)

            self.finish(json.dumps({
                "success": True,
                "migrated": result["migrated"],
                "errors": result["errors"],
                "message": f"Migrated {result['migrated']} cell states"
            }))

        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))


class CellStateStatsHandler(APIHandler):
    """Handler for cell state cache statistics"""

    @tornado.web.authenticated
    def get(self):
        """Get cell state cache statistics"""
        try:
            cell_state_manager = get_cell_state_cache_manager()
            stats = cell_state_manager.get_cache_stats()
            self.finish(json.dumps(stats))

        except Exception as e:
            self.set_status(500)
            self.finish(json.dumps({
                "error": "Internal server error",
                "message": str(e)
            }))
