#!/usr/bin/env python
"""Standalone Database Service Server.

Run as:
    python -m tc_db_base.server --port 5002
"""
import argparse
import logging
import os
import sys

from flask import Flask, jsonify, request
from flask_cors import CORS

from tc_db_base import init_db, get_repository, get_schema

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Create Flask application."""
    app = Flask(__name__)
    CORS(app)

    # Initialize database
    db = init_db()
    schema = get_schema()

    # Create indexes on startup
    db.ensure_all_indexes()

    # =========================================================================
    # Health Endpoints
    # =========================================================================

    @app.route('/')
    def index():
        return jsonify({
            'service': 'Database Module',
            'version': '1.0.0',
            'collections': schema.get_collection_names()
        })

    @app.route('/health')
    def health():
        health_status = db.health_check()
        status_code = 200 if health_status.get('status') == 'healthy' else 503
        return jsonify(health_status), status_code

    @app.route('/schema')
    def get_full_schema():
        return jsonify(schema.schema)

    @app.route('/schema/<collection_name>')
    def get_collection_schema(collection_name):
        coll_schema = schema.get_collection(collection_name)
        if not coll_schema:
            return jsonify({'error': 'Collection not found'}), 404
        return jsonify(coll_schema)

    # =========================================================================
    # Generic CRUD Endpoints
    # =========================================================================

    @app.route('/api/v1/<collection_name>', methods=['GET'])
    def list_documents(collection_name):
        """List documents."""
        repo = get_repository(collection_name)
        if not repo:
            return jsonify({'error': 'Collection not found'}), 404

        skip = request.args.get('skip', 0, type=int)
        limit = request.args.get('limit', 100, type=int)

        # Parse filter
        filter_param = request.args.get('filter')
        query = {}
        if filter_param:
            import json
            try:
                query = json.loads(filter_param)
            except:
                pass

        docs = repo.find_many(query, skip=skip, limit=limit)
        return jsonify({
            'collection': collection_name,
            'count': len(docs),
            'documents': docs
        })

    @app.route('/api/v1/<collection_name>/<doc_id>', methods=['GET'])
    def get_document(collection_name, doc_id):
        """Get document by ID."""
        repo = get_repository(collection_name)
        if not repo:
            return jsonify({'error': 'Collection not found'}), 404

        doc = repo.find_by_id(doc_id)
        if not doc:
            return jsonify({'error': 'Document not found'}), 404

        return jsonify(doc)

    @app.route('/api/v1/<collection_name>', methods=['POST'])
    def create_document(collection_name):
        """Create document."""
        repo = get_repository(collection_name)
        if not repo:
            return jsonify({'error': 'Collection not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400

        try:
            doc_id = repo.create(data)
            return jsonify({'success': True, 'id': doc_id}), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/v1/<collection_name>/<doc_id>', methods=['PUT', 'PATCH'])
    def update_document(collection_name, doc_id):
        """Update document."""
        repo = get_repository(collection_name)
        if not repo:
            return jsonify({'error': 'Collection not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400

        try:
            modified = repo.update_by_id(doc_id, data)
            return jsonify({'success': True, 'modified': modified})
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/api/v1/<collection_name>/<doc_id>', methods=['DELETE'])
    def delete_document(collection_name, doc_id):
        """Delete document."""
        repo = get_repository(collection_name)
        if not repo:
            return jsonify({'error': 'Collection not found'}), 404

        deleted = repo.delete_by_id(doc_id)
        return jsonify({'success': True, 'deleted': deleted})

    # =========================================================================
    # Search Endpoint
    # =========================================================================

    @app.route('/api/v1/<collection_name>/search', methods=['GET', 'POST'])
    def search_documents(collection_name):
        """Search documents."""
        repo = get_repository(collection_name)
        if not repo:
            return jsonify({'error': 'Collection not found'}), 404

        if request.method == 'POST':
            data = request.get_json() or {}
            text = data.get('q', data.get('text', ''))
            fields = data.get('fields')
            limit = data.get('limit', 20)
        else:
            text = request.args.get('q', '')
            fields = request.args.get('fields', '').split(',') if request.args.get('fields') else None
            limit = request.args.get('limit', 20, type=int)

        if not text:
            return jsonify({'error': 'Search text required'}), 400

        results = repo.search(text, fields=fields, limit=limit)
        return jsonify({
            'collection': collection_name,
            'query': text,
            'count': len(results),
            'results': results
        })

    # =========================================================================
    # Aggregation Endpoint
    # =========================================================================

    @app.route('/api/v1/<collection_name>/aggregate', methods=['POST'])
    def aggregate_documents(collection_name):
        """Run aggregation pipeline."""
        repo = get_repository(collection_name)
        if not repo:
            return jsonify({'error': 'Collection not found'}), 404

        data = request.get_json()
        pipeline = data.get('pipeline', [])

        if not pipeline:
            return jsonify({'error': 'Pipeline required'}), 400

        results = repo.aggregate(pipeline)
        return jsonify({
            'collection': collection_name,
            'results': results
        })

    @app.route('/api/v1/<collection_name>/count-by/<field>', methods=['GET'])
    def count_by_field(collection_name, field):
        """Count documents grouped by field."""
        repo = get_repository(collection_name)
        if not repo:
            return jsonify({'error': 'Collection not found'}), 404

        counts = repo.count_by(field)
        return jsonify({
            'collection': collection_name,
            'field': field,
            'counts': counts
        })

    return app


def main():
    parser = argparse.ArgumentParser(description='Database Module Server')
    parser.add_argument('--host', type=str, default='0.0.0.0')
    parser.add_argument('--port', type=int, default=5002)
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("DATABASE MODULE SERVER")
    logger.info("=" * 60)
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info("=" * 60)

    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()

