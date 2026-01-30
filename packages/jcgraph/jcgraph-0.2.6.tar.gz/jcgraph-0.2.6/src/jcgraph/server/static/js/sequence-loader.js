/**
 * 序列加载器 - 统一管理序列数据的加载
 *
 * 负责：
 * - API 调用
 * - 加载状态管理
 * - 参数传递
 */

class SequenceLoader {
    constructor() {
        this.cache = new Map(); // 缓存加载的数据
    }

    /**
     * 加载向下调用序列
     * @param {string} methodId - 方法ID
     * @param {Object} options - 选项
     * @returns {Promise<Object>}
     */
    async loadDownwardSequence(methodId, options = {}) {
        const {
            depth = 3,
            minImportance = 50,
            branches = {},
            useCache = false
        } = options;

        const cacheKey = `down:${methodId}:${depth}:${minImportance}:${JSON.stringify(branches)}`;

        if (useCache && this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        const url = `/api/graph/sequence/${encodeURIComponent(methodId)}?depth=${depth}`;

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    branches,
                    min_importance: minImportance
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (useCache) {
                this.cache.set(cacheKey, data);
            }

            return data;
        } catch (error) {
            console.error('加载向下序列失败:', error);
            throw error;
        }
    }

    /**
     * 加载向上调用序列
     * @param {string} methodId - 方法ID
     * @param {Object} options - 选项
     * @returns {Promise<Object>}
     */
    async loadUpwardSequence(methodId, options = {}) {
        const {
            depth = 3,
            minImportance = 50,
            useCache = false
        } = options;

        const cacheKey = `up:${methodId}:${depth}:${minImportance}`;

        if (useCache && this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        const url = `/api/graph/callers-sequence/${encodeURIComponent(methodId)}?depth=${depth}&min_importance=${minImportance}`;

        try {
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (useCache) {
                this.cache.set(cacheKey, data);
            }

            return data;
        } catch (error) {
            console.error('加载向上序列失败:', error);
            throw error;
        }
    }

    /**
     * 清除缓存
     */
    clearCache() {
        this.cache.clear();
    }

    /**
     * 移除特定缓存
     */
    removeCacheFor(methodId) {
        for (const key of this.cache.keys()) {
            if (key.includes(methodId)) {
                this.cache.delete(key);
            }
        }
    }
}

// 创建全局实例
window.sequenceLoader = new SequenceLoader();
