"""调用序列构建器 - 不依赖 FastAPI 的核心逻辑

本模块提供调用时序树构建功能，可被 MCP Server 和 Web API 复用。
只依赖 Storage 和 Python 标准库，不依赖 FastAPI。
"""

from jcgraph.storage.sqlite import Storage


def calculate_importance(
    node: dict,
    call_stats: dict,
    depth: int = 0,
    is_branch_point: bool = False
) -> tuple[int, str]:
    """
    计算节点重要度 (基于客观维度)

    Args:
        node: 节点信息
        call_stats: 调用统计 {"method_id": {"in_degree": N, "out_degree": M}}
        depth: 调用深度
        is_branch_point: 是否是分支点

    Returns:
        (score, level): 分数和等级
    """
    score = 50  # 基础分数
    node_id = node.get('id', '')
    stats = call_stats.get(node_id, {"in_degree": 0, "out_degree": 0})

    # 1. 结构特征 (+25)
    if node.get('subtype') == 'abstract':
        score += 20

    if is_branch_point:
        score += 15

    # 2. 调用关系 - 入度 (+/-30)
    in_degree = stats.get('in_degree', 0)
    if in_degree == 0:
        score += 10  # 入口方法
    elif in_degree <= 2:
        score += 5   # 专用实现
    elif in_degree <= 5:
        pass         # 正常,不加不减
    elif in_degree <= 10:
        score -= 10  # 较通用
    else:
        score -= 20  # 工具类

    # 3. 调用关系 - 出度 (+/-30)
    out_degree = stats.get('out_degree', 0)
    if out_degree > 10:
        score += 10  # 协调者/编排者
    elif out_degree >= 5:
        score += 5   # 有一定复杂度
    elif out_degree >= 1:
        pass         # 正常
    else:
        score -= 5   # 叶子节点/简单方法

    # 4. 代码特征 - 行数 (+15)
    line_start = node.get('line_start', 0)
    line_end = node.get('line_end', 0)
    line_count = line_end - line_start if line_end > line_start else 0

    if line_count > 50:
        score += 10  # 复杂逻辑
    elif line_count > 20:
        score += 5   # 中等复杂度

    # 5. 调用深度
    if depth >= 3:
        score += 5   # 深层实现

    # 分数限制在 [0, 100]
    score = max(0, min(100, score))

    # 分级
    if score >= 70:
        level = 'CRITICAL'
    elif score >= 50:
        level = 'IMPORTANT'
    elif score >= 30:
        level = 'NORMAL'
    else:
        level = 'AUXILIARY'

    return score, level


def build_call_sequence_tree(
    storage: Storage,
    node_id: str,
    depth: int = 3,
    branches: dict = None,
    min_importance: int = 50
) -> dict:
    """
    构建调用时序树 - 核心逻辑（可复用）

    参数:
        - storage: Storage 实例
        - node_id: 方法ID
        - depth: 追踪深度
        - branches: 分支选择 {"method_id": "implementation_id"}
        - min_importance: 最小重要度阈值，低于此值的节点不展开（默认50）

    返回: 时序树 dict

    异常: ValueError - 方法不存在
    """
    if branches is None:
        branches = {}

    # 获取当前方法的project_id用于统计
    root_method = storage.get_node(node_id)
    if not root_method:
        raise ValueError(f"方法不存在: {node_id}")

    project_id = root_method.get('project_id')

    # 预计算调用统计
    call_stats = storage.calculate_call_statistics(project_id)

    # 收集所有分支点信息
    branch_points = []

    def build_sequence(method_id: str, current_depth: int = 0):
        if current_depth >= depth:
            return None

        # 获取方法信息
        method = storage.get_node(method_id)
        if not method or method['type'] != 'method':
            return None

        # 获取该方法的所有调用
        edges = storage.get_edges_from(method_id)

        # 如果是接口方法且没有出边，尝试查找实现类的同名方法
        if not edges or len(edges) == 0:
            # 检查是否是接口方法（通过parent_id查找类是否是interface）
            parent_id = method.get('parent_id')
            if parent_id:
                parent_node = storage.get_node(parent_id)
                if parent_node and parent_node.get('type') == 'interface':
                    # 查找实现该接口的类
                    cursor = storage.conn.cursor()
                    cursor.execute("""
                        SELECT source_id FROM edges
                        WHERE target_id = ? AND relation_type = 'IMPLEMENTS'
                        LIMIT 1
                    """, (parent_id,))
                    impl_row = cursor.fetchone()

                    if impl_row:
                        impl_class_id = impl_row['source_id']
                        method_name = method['name']
                        impl_method_id = f"{impl_class_id}#{method_name}"

                        # 检查实现类的方法是否存在
                        impl_method = storage.get_node(impl_method_id)
                        if impl_method:
                            # 递归查询实现类的方法
                            return build_sequence(impl_method_id, current_depth)

        calls = []
        for edge in edges:
            if edge['relation_type'] != 'CALLS':
                continue

            target_id = edge['target_id']

            # 提取新字段
            loop_type = edge.get('loop_type')
            loop_id = edge.get('loop_id')
            is_interface_call = edge.get('is_interface_call', 0)
            lambda_depth = edge.get('lambda_depth', 0)
            # 分支字段
            branch_type = edge.get('branch_type')
            branch_id = edge.get('branch_id')
            branch_condition = edge.get('branch_condition')
            branch_order = edge.get('branch_order', 0)

            if not target_id:
                # 未解析的调用，显示原始文本
                calls.append({
                    'line': edge['line_number'],
                    'raw': edge['target_raw'],
                    'resolved': False,
                    'loop_type': loop_type,
                    'loop_id': loop_id,
                    'is_interface_call': is_interface_call,
                    'lambda_depth': lambda_depth,
                    'branch_type': branch_type,
                    'branch_id': branch_id,
                    'branch_condition': branch_condition,
                    'branch_order': branch_order
                })
                continue

            # 检查目标方法是否是抽象方法（有多个实现）
            target_method = storage.get_node(target_id)
            if not target_method:
                # 外部依赖调用（有 target_id 但方法定义不在本项目中）
                calls.append({
                    'line': edge['line_number'],
                    'raw': edge.get('target_raw', target_id),
                    'resolved': True,  # resolved=1 表示知道调用了什么方法
                    'external': True,  # 标记为外部依赖
                    'target_id': target_id,  # 保留完整方法 ID
                    'loop_type': loop_type,
                    'loop_id': loop_id,
                    'is_interface_call': is_interface_call,
                    'lambda_depth': lambda_depth,
                    'branch_type': branch_type,
                    'branch_id': branch_id,
                    'branch_condition': branch_condition,
                    'branch_order': branch_order
                })
                continue

            # 检查是否是abstract方法或edge标记为接口调用
            is_abstract = target_method.get('subtype') == 'abstract'
            is_interface_call_flag = is_interface_call == 1
            implementations = []

            if is_abstract or is_interface_call_flag:
                # 查询所有实现
                implementations = storage.get_implementations(target_id)

                if implementations:
                    # 这是一个分支点
                    # 检查用户是否选择了特定实现
                    selected_impl_id = branches.get(target_id)

                    if selected_impl_id:
                        # 用户选择了特定实现，使用它
                        actual_target_id = selected_impl_id
                    else:
                        # 默认使用第一个实现
                        actual_target_id = implementations[0]['id']

                    # 检查实现方法的重要度
                    impl_method_node = storage.get_node(actual_target_id)
                    if impl_method_node:
                        impl_score_check, _ = calculate_importance(
                            impl_method_node, call_stats, current_depth + 1, True
                        )
                        should_expand_impl = impl_score_check >= min_importance
                    else:
                        should_expand_impl = True  # 找不到节点，默认展开

                    # 递归构建选中实现的调用链（如果满足重要度）
                    sub_sequence = build_sequence(actual_target_id, current_depth + 1) if should_expand_impl else None

                    # 构建分支点信息
                    branch_info = {
                        'abstract_method_id': target_id,
                        'abstract_method_name': target_method['name'],
                        'implementations': [
                            {
                                'id': impl['id'],
                                'class_name': impl['class_name'],
                                'branch_label': impl['branch_label']
                            }
                            for impl in implementations
                        ],
                        'selected_id': actual_target_id
                    }
                    branch_points.append(branch_info)

                    if sub_sequence:
                        calls.append({
                            'line': edge['line_number'],
                            'method': sub_sequence['method'],
                            'calls': sub_sequence.get('calls', []),
                            'resolved': True,
                            'is_branch_point': True,
                            'branch_info': branch_info,
                            'loop_type': loop_type,
                            'loop_id': loop_id,
                            'is_interface_call': is_interface_call,
                            'lambda_depth': lambda_depth,
                            'branch_type': branch_type,
                            'branch_id': branch_id,
                            'branch_condition': branch_condition,
                            'branch_order': branch_order,
                            'implementations': [
                                {
                                    'id': impl['id'],
                                    'class_name': impl['class_name'],
                                    'branch_label': impl['branch_label']
                                }
                                for impl in implementations
                            ]
                        })
                    else:
                        # 深度限制或重要度过滤
                        impl_method = storage.get_node(actual_target_id)
                        if impl_method:
                            impl_score, impl_level = calculate_importance(
                                impl_method, call_stats, current_depth + 1, True
                            )
                            node_data = {
                                'line': edge['line_number'],
                                'method': {
                                    'id': impl_method['id'],
                                    'name': impl_method['name'],
                                    'type': impl_method['type'],
                                    'signature': impl_method.get('signature', ''),
                                    'return_type': impl_method.get('return_type', 'void'),
                                    'class_name': impl_method.get('class_name', ''),
                                    'importance_score': impl_score,
                                    'importance_level': impl_level
                                },
                                'calls': [],
                                'resolved': True,
                                'is_branch_point': True,
                                'branch_info': branch_info,
                                'loop_type': loop_type,
                                'loop_id': loop_id,
                                'is_interface_call': is_interface_call,
                                'lambda_depth': lambda_depth,
                                'branch_type': branch_type,
                                'branch_id': branch_id,
                                'branch_condition': branch_condition,
                                'branch_order': branch_order,
                                'implementations': [
                                    {
                                        'id': impl['id'],
                                        'class_name': impl['class_name'],
                                        'branch_label': impl['branch_label']
                                    }
                                    for impl in implementations
                                ]
                            }
                            # 只添加满足重要度阈值的分支点
                            if should_expand_impl:
                                calls.append(node_data)
                            # else: 重要度低于阈值，完全跳过该分支点
                    continue

            # 普通方法调用（非分支点）
            # 先获取目标方法信息，计算重要度
            target = storage.get_node(target_id)
            if not target:
                continue

            target_score, target_level = calculate_importance(
                target, call_stats, current_depth + 1, False
            )

            # 检查是否需要递归展开：重要度 >= min_importance
            should_expand = target_score >= min_importance

            # 只添加满足重要度阈值的节点
            if should_expand:
                # 递归构建子调用
                sub_sequence = build_sequence(target_id, current_depth + 1)
                if sub_sequence:
                    calls.append({
                        'line': edge['line_number'],
                        'method': sub_sequence['method'],
                        'calls': sub_sequence.get('calls', []),
                        'resolved': True,
                        'is_branch_point': False,
                        'loop_type': loop_type,
                        'loop_id': loop_id,
                        'is_interface_call': is_interface_call,
                        'lambda_depth': lambda_depth,
                        'branch_type': branch_type,
                        'branch_id': branch_id,
                        'branch_condition': branch_condition,
                        'branch_order': branch_order
                    })
                else:
                    # 深度限制，显示节点但不展开
                    calls.append({
                        'line': edge['line_number'],
                        'method': {
                            'id': target['id'],
                            'name': target['name'],
                            'type': target['type'],
                            'signature': target.get('signature', ''),
                            'return_type': target.get('return_type', 'void'),
                            'importance_score': target_score,
                            'importance_level': target_level
                        },
                        'calls': [],
                        'resolved': True,
                        'is_branch_point': False,
                        'loop_type': loop_type,
                        'loop_id': loop_id,
                        'is_interface_call': is_interface_call,
                        'lambda_depth': lambda_depth,
                        'branch_type': branch_type,
                        'branch_id': branch_id,
                        'branch_condition': branch_condition,
                        'branch_order': branch_order
                    })
            # else: 重要度低于阈值，完全跳过该节点

        # 计算重要度（注意：这里的is_branch_point指的是当前方法本身是否是抽象方法）
        is_abstract_method = method.get('subtype') == 'abstract'
        importance_score, importance_level = calculate_importance(
            method, call_stats, current_depth, is_abstract_method
        )

        return {
            'method': {
                'id': method['id'],
                'name': method['name'],
                'full_name': method['full_name'],
                'signature': method.get('signature', ''),
                'return_type': method.get('return_type', 'void'),
                'params': method.get('params', []),
                'project_id': method.get('project_id'),
                'class_name': method.get('class_name', ''),
                'file_path': method.get('file_path', ''),
                'line_start': method.get('line_start', 0),
                'line_end': method.get('line_end', 0),
                'subtype': method.get('subtype', 'normal'),
                'importance_score': importance_score,
                'importance_level': importance_level
            },
            'calls': calls
        }

    result = build_sequence(node_id)
    if not result:
        raise ValueError("方法不存在或不是方法类型")

    # 添加分支点信息到返回结果
    result['branch_points'] = branch_points

    return result


def build_caller_sequence_tree(
    storage: Storage,
    node_id: str,
    depth: int = 3,
    branches: dict = None,
    min_importance: int = 50
) -> dict:
    """
    构建向上调用时序树（谁调用了我）- 核心逻辑

    参数:
        - storage: Storage 实例
        - node_id: 方法ID
        - depth: 追踪深度
        - branches: 分支选择（暂未使用，保留接口一致性）
        - min_importance: 最小重要度阈值，低于此值的节点不展开（默认50）

    返回: 时序树 dict

    异常: ValueError - 方法不存在
    """
    if branches is None:
        branches = {}

    # 获取当前方法的project_id用于统计
    root_method = storage.get_node(node_id)
    if not root_method:
        raise ValueError(f"方法不存在: {node_id}")

    project_id = root_method.get('project_id')

    # 预计算调用统计
    call_stats = storage.calculate_call_statistics(project_id)

    def build_sequence(method_id: str, current_depth: int = 0, visited: set = None):
        if visited is None:
            visited = set()

        if current_depth >= depth:
            return None

        # 防止循环调用
        if method_id in visited:
            return None

        visited.add(method_id)

        # 获取方法信息
        method = storage.get_node(method_id)
        if not method or method['type'] != 'method':
            return None

        # 获取调用该方法的所有边（包括虚拟边）
        edges = storage.get_edges_to(method_id)

        # 检查当前方法是否覆写了父类/接口方法
        # 如果是，则也需要查找父类方法的调用者
        # 因为调用父类方法的代码在运行时会分派到子类实现
        cursor = storage.conn.cursor()
        cursor.execute("""
            SELECT target_id FROM edges
            WHERE source_id = ? AND relation_type = 'OVERRIDES'
        """, (method_id,))
        override_row = cursor.fetchone()

        if override_row:
            parent_method_id = override_row['target_id']
            # 获取调用父类方法的边
            parent_edges = storage.get_edges_to(parent_method_id)
            # 去重：使用集合记录已有的 source_id
            existing_sources = {edge['source_id'] for edge in edges if edge.get('relation_type') in ('CALLS', 'VIRTUAL_CALL')}
            # 合并到当前边列表（只添加不重复的）
            for parent_edge in parent_edges:
                if parent_edge['relation_type'] in ('CALLS', 'VIRTUAL_CALL'):
                    source_id = parent_edge['source_id']
                    if source_id not in existing_sources:
                        # 创建一个副本并标记
                        inherited_edge = parent_edge.copy()
                        inherited_edge['inherited_from_override'] = parent_method_id
                        edges.append(inherited_edge)
                        existing_sources.add(source_id)

        callers = []
        for edge in edges:
            # 接受 CALLS 和 VIRTUAL_CALL 两种关系类型
            if edge['relation_type'] not in ('CALLS', 'VIRTUAL_CALL'):
                continue

            source_id = edge['source_id']
            is_virtual = edge.get('is_virtual', 0)
            via_interface_id = edge.get('via_interface_id')

            if not source_id:
                continue

            # 获取调用者方法信息
            caller_method = storage.get_node(source_id)
            if not caller_method:
                # 外部调用者
                callers.append({
                    'line': edge['line_number'],
                    'raw': edge.get('target_raw', ''),
                    'resolved': False,
                    'external': True,
                    'source_id': source_id,
                    'is_virtual': 0,  # 调用者本身不是虚拟的
                    'via_interface_id': None
                })
                continue

            # 计算调用者重要度
            caller_score, caller_level = calculate_importance(
                caller_method, call_stats, current_depth + 1, False
            )

            # 检查是否需要递归展开：重要度 >= min_importance
            should_expand = caller_score >= min_importance

            # 只添加满足重要度阈值的节点
            if should_expand:
                # 递归构建调用者的调用链
                sub_sequence = build_sequence(source_id, current_depth + 1, visited.copy())
                if sub_sequence:
                    callers.append({
                        'line': edge['line_number'],
                        'method': sub_sequence['method'],
                        'callers': sub_sequence.get('callers', []),
                        'resolved': True,
                        'is_virtual': 0,  # 调用者本身不是虚拟的
                        'via_interface_id': None,
                        'target_raw': edge.get('target_raw', '')
                    })
                else:
                    # 深度限制，显示节点但不展开
                    callers.append({
                        'line': edge['line_number'],
                        'method': {
                            'id': caller_method['id'],
                            'name': caller_method['name'],
                            'type': caller_method['type'],
                            'signature': caller_method.get('signature', ''),
                            'return_type': caller_method.get('return_type', 'void'),
                            'class_name': caller_method.get('class_name', ''),
                            'importance_score': caller_score,
                            'importance_level': caller_level
                        },
                        'callers': [],
                        'resolved': True,
                        'is_virtual': 0,  # 调用者本身不是虚拟的
                        'via_interface_id': None,
                        'target_raw': edge.get('target_raw', '')
                    })

        # 计算当前方法的重要度
        is_abstract_method = method.get('subtype') == 'abstract'
        importance_score, importance_level = calculate_importance(
            method, call_stats, current_depth, is_abstract_method
        )

        return {
            'method': {
                'id': method['id'],
                'name': method['name'],
                'full_name': method['full_name'],
                'signature': method.get('signature', ''),
                'return_type': method.get('return_type', 'void'),
                'params': method.get('params', []),
                'project_id': method.get('project_id'),
                'class_name': method.get('class_name', ''),
                'file_path': method.get('file_path', ''),
                'line_start': method.get('line_start', 0),
                'line_end': method.get('line_end', 0),
                'subtype': method.get('subtype', 'normal'),
                'importance_score': importance_score,
                'importance_level': importance_level
            },
            'callers': callers
        }

    result = build_sequence(node_id)
    if not result:
        raise ValueError("方法不存在或不是方法类型")

    return result
