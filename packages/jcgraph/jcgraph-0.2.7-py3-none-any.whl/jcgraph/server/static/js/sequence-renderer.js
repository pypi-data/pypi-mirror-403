/**
 * 序列图渲染器 - 通用的调用序列树渲染模块
 *
 * 支持：
 * - 向下调用序列（callees）
 * - 向上调用序列（callers）
 * - 循环、分支、Lambda 等结构
 * - 虚拟边高亮
 * - 折叠/展开
 */

class SequenceRenderer {
    constructor(options = {}) {
        this.nodeIdCounter = 0;
        this.direction = options.direction || 'down'; // 'down' 或 'up'
        this.onMethodClick = options.onMethodClick || (() => {});
        this.onCodeView = options.onCodeView || (() => {});
    }

    /**
     * 渲染序列树的入口方法
     * @param {Object} data - API 返回的序列数据
     * @param {string} direction - 'down' 或 'up'
     * @returns {string} HTML 字符串
     */
    render(data, direction = 'down') {
        this.direction = direction;
        this.nodeIdCounter = 0;

        if (!data) return '<div class="text-gray-500">暂无数据</div>';

        if (direction === 'down') {
            return this.renderDownwardSequence(data, 0);
        } else {
            // 反转调用者树：从顶层调用者到当前方法
            const reversed = this.reverseCallerTree(data);
            return this.renderReversedCallerTree(reversed, 0, data.method.id);
        }
    }

    /**
     * 反转调用者树结构 - 简化版本,直接遍历渲染
     * 不需要真正反转数据结构,而是在渲染时按正确顺序输出
     */
    reverseCallerTree(node) {
        // 收集从根到叶的所有路径
        const paths = [];

        function collectPaths(currentNode, path) {
            const newPath = [...path, currentNode];

            if (!currentNode.callers || currentNode.callers.length === 0) {
                // 到达叶子节点,保存路径
                paths.push(newPath);
            } else {
                // 继续递归
                for (const caller of currentNode.callers) {
                    collectPaths(caller, newPath);
                }
            }
        }

        collectPaths(node, []);

        // 将路径转换为树结构(从顶层调用者开始)
        // 为了保持树结构,我们需要去重合并相同的节点
        return this.buildTreeFromPaths(paths);
    }

    /**
     * 从路径列表构建树结构
     */
    buildTreeFromPaths(paths) {
        if (paths.length === 0) return null;

        // 反转每条路径,使其从顶层调用者开始
        const reversedPaths = paths.map(path => [...path].reverse());

        // 构建树的递归函数
        function buildNode(pathsAtThisLevel, depth = 0) {
            if (pathsAtThisLevel.length === 0) return [];

            // 按当前深度的方法ID分组
            const groups = new Map();
            for (const path of pathsAtThisLevel) {
                if (path.length > depth) {
                    const methodId = path[depth].method?.id;
                    if (!groups.has(methodId)) {
                        groups.set(methodId, {
                            node: path[depth],
                            childPaths: []
                        });
                    }
                    groups.get(methodId).childPaths.push(path);
                }
            }

            // 构建节点
            const result = [];
            for (const [methodId, {node, childPaths}] of groups) {
                const children = buildNode(childPaths, depth + 1);
                result.push({
                    method: node.method,
                    resolved: node.resolved,
                    calls: children
                });
            }

            return result;
        }

        const rootNodes = buildNode(reversedPaths, 0);

        // 如果只有一个根节点,直接返回
        if (rootNodes.length === 1) {
            return rootNodes[0];
        }

        // 多个根节点,返回虚拟根
        return {
            method: null,
            calls: rootNodes
        };
    }

    /**
     * 渲染反转后的调用者树
     */
    renderReversedCallerTree(node, depth, targetMethodId) {
        if (!node) return '';

        let html = '';

        // 如果是虚拟根节点，直接渲染子节点
        if (!node.method) {
            if (node.calls) {
                for (const call of node.calls) {
                    html += this.renderReversedCallerNode(call, depth, targetMethodId);
                }
            }
            return html;
        }

        // 渲染普通节点
        return this.renderReversedCallerNode(node, depth, targetMethodId);
    }

    /**
     * 渲染反转调用者树的单个节点
     */
    renderReversedCallerNode(node, depth, targetMethodId) {
        const nodeId = `node-${this.nodeIdCounter++}`;
        const indent = depth * 20;
        const method = node.method;
        const isTarget = method && method.id === targetMethodId;
        const hasChildren = node.calls && node.calls.length > 0;

        // 如果没有 method (虚拟根节点),跳过渲染直接递归子节点
        if (!method) {
            let html = '';
            if (hasChildren) {
                for (const call of node.calls) {
                    html += this.renderReversedCallerNode(call, depth, targetMethodId);
                }
            }
            return html;
        }

        const importance = method?.importance_level?.toLowerCase() || 'normal';
        const highlightClass = isTarget ? ' bg-yellow-100 font-bold' : '';

        let html = `<div class="sequence-node importance-${importance}${highlightClass}" style="padding-left: ${indent}px" id="${nodeId}">`;

        // 折叠按钮
        if (hasChildren) {
            html += `<span class="fold-btn" onclick="window.sequenceRenderer.toggleNode('${nodeId}')">[-]</span>`;
        } else {
            html += `<span class="fold-btn" style="visibility: hidden;">[-]</span>`;
        }

        // 重要度圆点
        html += `<span class="importance-dot"></span>`;

        // 方法名
        html += `<span class="method-name cursor-pointer" onclick="window.app_instance.openCodeModal('${method.id}')">${method.name}()</span>`;

        // 目标标识
        if (isTarget) {
            html += `<span class="ml-2 text-xs text-orange-600">← 当前方法</span>`;
        }

        html += '</div>';

        // 递归渲染子节点
        if (hasChildren) {
            html += `<div id="children-${nodeId}" class="sequence-children">`;
            for (const call of node.calls) {
                html += this.renderReversedCallerNode(call, depth + 1, targetMethodId);
            }
            html += '</div>';
        }

        return html;
    }

    /**
     * 渲染向下调用序列
     */
    renderDownwardSequence(node, depth) {
        if (!node || !node.calls) {
            return '';
        }

        let html = '';

        // 按 loop_id 和 branch_id 分组
        const groups = this.groupCalls(node.calls);

        // 渲染非分组调用
        for (const call of groups.plain) {
            html += this.renderCall(call, depth, 'down');
        }

        // 渲染循环组
        for (const [loopId, calls] of groups.loops) {
            html += this.renderLoopGroup(loopId, calls, depth, 'down');
        }

        // 渲染分支组
        for (const [branchId, calls] of groups.branches) {
            html += this.renderBranchGroup(branchId, calls, depth, 'down');
        }

        return html;
    }

    /**
     * 渲染向上调用序列
     */
    renderUpwardSequence(node, depth) {
        if (!node) {
            return '';
        }

        let html = '';

        // 如果有 callers，递归渲染每个调用者及其子调用者
        if (node.callers && node.callers.length > 0) {
            for (const caller of node.callers) {
                html += this.renderCallerNode(caller, depth);
            }
        }

        return html;
    }

    /**
     * 渲染单个调用者节点及其所有上层调用者
     */
    renderCallerNode(caller, depth) {
        const nodeId = `node-${this.nodeIdCounter++}`;
        const indent = depth * 20;

        // 未解析的调用
        if (!caller.resolved || !caller.method) {
            return this.renderUnresolvedCall(caller, indent);
        }

        const method = caller.method;
        const importance = method.importance_level?.toLowerCase() || 'normal';
        const hasCallers = caller.callers && caller.callers.length > 0;

        let html = `<div class="sequence-node importance-${importance}" style="padding-left: ${indent}px" id="${nodeId}">`;

        // 折叠按钮
        if (hasCallers) {
            html += `<span class="fold-btn" onclick="window.sequenceRenderer.toggleNode('${nodeId}')">[-]</span>`;
        } else {
            html += `<span class="fold-btn" style="visibility: hidden;">[-]</span>`;
        }

        // 重要度圆点
        html += `<span class="importance-dot"></span>`;

        // 虚拟边标识
        if (caller.is_virtual) {
            html += `<span class="virtual-call-indicator">🔗</span>`;
        }

        // 方法名
        html += `<span class="method-name cursor-pointer" onclick="window.app_instance.openCodeModal('${method.id}')">${method.name}()</span>`;

        // 虚拟边详情
        if (caller.is_virtual && caller.via_interface_id) {
            const interfaceMethod = caller.via_interface_id.split('#').pop();
            html += `<span class="virtual-call-tag ml-2">通过 ${interfaceMethod}</span>`;
        }

        html += '</div>';

        // 递归渲染上层调用者
        if (hasCallers) {
            html += `<div id="children-${nodeId}" class="sequence-children">`;
            html += this.renderUpwardSequence(caller, depth + 1);
            html += '</div>';
        }

        return html;
    }

    /**
     * 分组调用（按循环和分支）
     */
    groupCalls(calls) {
        const loops = new Map();
        const branches = new Map();
        const plain = [];

        const processedBranches = new Set();

        for (const call of calls) {
            // 分支优先
            if (call.branch_id && !processedBranches.has(call.branch_id)) {
                const branchCalls = calls.filter(c => c.branch_id === call.branch_id);
                branches.set(call.branch_id, branchCalls.sort((a, b) => a.branch_order - b.branch_order));
                processedBranches.add(call.branch_id);
            } else if (call.loop_id) {
                if (!loops.has(call.loop_id)) {
                    loops.set(call.loop_id, []);
                }
                loops.get(call.loop_id).push(call);
            } else if (!call.branch_id) {
                plain.push(call);
            }
        }

        return { loops, branches, plain };
    }

    /**
     * 渲染单个调用节点
     */
    renderCall(call, depth, direction) {
        const nodeId = `node-${this.nodeIdCounter++}`;
        const indent = depth * 20;

        // 未解析的调用
        if (!call.resolved || !call.method) {
            return this.renderUnresolvedCall(call, indent);
        }

        const method = call.method;
        const importance = method.importance_level?.toLowerCase() || 'normal';
        const hasChildren = direction === 'down'
            ? (call.calls && call.calls.length > 0)
            : (call.callers && call.callers.length > 0);

        let html = `<div class="sequence-node importance-${importance}" style="padding-left: ${indent}px" id="${nodeId}">`;

        // 折叠按钮
        if (hasChildren) {
            html += `<span class="fold-btn" onclick="window.sequenceRenderer.toggleNode('${nodeId}')">[-]</span>`;
        } else {
            html += `<span class="fold-btn" style="visibility: hidden;">[-]</span>`;
        }

        // 重要度圆点
        html += `<span class="importance-dot"></span>`;

        // 虚拟边标识
        if (call.is_virtual) {
            html += `<span class="virtual-call-indicator">🔗</span>`;
        }

        // 方法名
        html += `<span class="method-name cursor-pointer" onclick="window.app_instance.openCodeModal('${method.id}')">${method.name}()</span>`;

        // 虚拟边详情
        if (call.is_virtual && call.via_interface_id) {
            const interfaceMethod = call.via_interface_id.split('#').pop();
            html += `<span class="virtual-call-tag ml-2">通过 ${interfaceMethod}</span>`;
        }

        // 分支标签
        if (call.branch_condition) {
            const condition = this.escapeHtml(call.branch_condition);
            html += `<span class="branch-condition ml-2" title="${condition}">${condition}</span>`;
        }

        html += '</div>';

        // 子调用
        if (hasChildren) {
            html += `<div id="children-${nodeId}" class="sequence-children">`;
            if (direction === 'down') {
                html += this.renderDownwardSequence(call, depth + 1);
            } else {
                html += this.renderUpwardSequence(call, depth + 1);
            }
            html += '</div>';
        }

        return html;
    }

    /**
     * 渲染未解析的调用
     */
    renderUnresolvedCall(call, indent) {
        return `<div class="sequence-node text-gray-400" style="padding-left: ${indent}px">
            <span class="fold-btn" style="visibility: hidden;">[-]</span>
            <span class="importance-dot" style="background: #ddd;"></span>
            <span>${this.escapeHtml(call.raw || call.target_raw || '未知调用')}</span>
        </div>`;
    }

    /**
     * 渲染循环组
     */
    renderLoopGroup(loopId, calls, depth, direction) {
        const loopType = calls[0]?.loop_type || 'for';
        const indent = depth * 20;

        let html = `<div class="loop-group" style="padding-left: ${indent}px">`;
        html += `<div class="loop-header">`;
        html += `<span class="loop-tag">${loopType.toUpperCase()}</span>`;
        html += `</div>`;

        for (const call of calls) {
            html += this.renderCall(call, depth, direction);
        }

        html += '</div>';
        return html;
    }

    /**
     * 渲染分支组
     */
    renderBranchGroup(branchId, calls, depth, direction) {
        const branchType = calls[0]?.branch_type || 'if';
        const indent = depth * 20;

        let html = `<div class="branch-group" style="padding-left: ${indent}px">`;

        for (let i = 0; i < calls.length; i++) {
            const call = calls[i];
            const isFirst = i === 0;

            if (isFirst) {
                html += `<div class="branch-header">`;
                html += `<span class="branch-tag">${branchType.toUpperCase()}</span>`;
                html += '</div>';
            }

            html += this.renderCall(call, depth, direction);
        }

        html += '</div>';
        return html;
    }

    /**
     * 切换节点折叠状态
     */
    toggleNode(nodeId) {
        const childrenDiv = document.getElementById(`children-${nodeId}`);
        if (!childrenDiv) return;

        const isFolded = childrenDiv.classList.contains('folded');
        const parentNode = document.getElementById(nodeId);
        const foldBtn = parentNode?.querySelector('.fold-btn');

        if (isFolded) {
            // 展开
            childrenDiv.classList.remove('folded');
            if (foldBtn) foldBtn.textContent = '[-]';
        } else {
            // 折叠
            childrenDiv.classList.add('folded');
            const childCount = childrenDiv.querySelectorAll(':scope > .sequence-node').length;
            if (foldBtn) foldBtn.textContent = `[+${childCount}]`;
        }
    }

    /**
     * HTML 转义
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 统计调用数量
     */
    countNodes(node, direction = 'down') {
        if (!node) return 0;

        const children = direction === 'down' ? node.calls : node.callers;
        if (!children || children.length === 0) return 0;

        let count = children.length;
        for (const child of children) {
            count += this.countNodes(child, direction);
        }

        return count;
    }
}

// 创建全局实例
window.sequenceRenderer = new SequenceRenderer();
