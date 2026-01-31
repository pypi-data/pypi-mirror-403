# -*- coding: utf-8 -*-
"""
web_exporter_solid.py - Web 导出器（实体模式）

将 Model3D 导出为带截面实体的 HTML 查看器
"""

import json
from typing import Dict
from .web_exporter import WebExporter
from .mesh_generator import MeshGenerator
from ..geometry.element_geometry import Model3D, FrameElement3D, CableElement3D


class WebExporterSolid(WebExporter):
    """Web 导出器 - 实体模式"""
    
    def __init__(self, num_segments: int = 16):
        """
        初始化
        
        Args:
            num_segments: 圆形截面的分段数（8/12/16/24/32）
        """
        super().__init__()
        self.mesh_generator = MeshGenerator(num_segments=num_segments)
        self.num_segments = num_segments
    
    def _generate_geometry(self, model_3d: Model3D) -> Dict:
        """生成实体几何数据"""
        all_vertices = []
        all_normals = []
        all_colors = []
        all_indices = []
        vertex_offset = 0
        
        print(f"  生成实体网格（{self.num_segments}段）...")
        
        for i, elem in enumerate(model_3d.elements):
            # 确定颜色
            if isinstance(elem, FrameElement3D):
                color = (0.2, 0.5, 0.9)  # 蓝色
            elif isinstance(elem, CableElement3D):
                color = (0.9, 0.2, 0.2)  # 红色
            else:
                color = (0.5, 0.5, 0.5)  # 灰色
            
            # 生成网格
            mesh = self.mesh_generator.generate_element_mesh(elem, color)
            
            # 合并数据
            all_vertices.extend(mesh.vertices)
            all_normals.extend(mesh.normals)
            all_colors.extend(mesh.colors)
            
            # 调整索引偏移
            adjusted_indices = [idx + vertex_offset for idx in mesh.indices]
            all_indices.extend(adjusted_indices)
            
            vertex_offset += len(mesh.vertices) // 3
            
            if (i + 1) % 10 == 0:
                print(f"    已处理 {i + 1}/{len(model_3d.elements)} 个单元")
        
        print(f"  ✓ 网格生成完成")
        print(f"    顶点数: {len(all_vertices) // 3}")
        print(f"    三角形数: {len(all_indices) // 3}")
        
        return {
            "vertices": all_vertices,
            "normals": all_normals,
            "colors": all_colors,
            "indices": all_indices,
            "mode": "solid"
        }
    
    def _generate_html(self, geometry_data: Dict, model_name: str) -> str:
        """生成 HTML 内容（实体模式）"""
        
        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{model_name} - SAP2000 模型查看器（实体）</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            overflow: hidden;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        
        #container {{
            width: 100vw;
            height: 100vh;
        }}
        
        #info {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            max-width: 300px;
            z-index: 100;
        }}
        
        #info h1 {{
            font-size: 18px;
            margin-bottom: 10px;
            color: #333;
        }}
        
        #info p {{
            font-size: 14px;
            color: #666;
            margin: 5px 0;
        }}
        
        .badge {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 12px;
            margin-left: 5px;
        }}
        
        .legend {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #ddd;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 8px 0;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
            margin-right: 10px;
        }}
        
        .controls {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: rgba(255, 255, 255, 0.95);
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 100;
        }}
        
        .controls button {{
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 5px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }}
        
        .controls button:hover {{
            background: #5568d3;
        }}
        
        .controls button.active {{
            background: #4CAF50;
        }}
        
        #loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            z-index: 200;
        }}
        
        .spinner {{
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div id="loading">
        <div class="spinner"></div>
        <p>加载模型中...</p>
    </div>
    
    <div id="container"></div>
    
    <div id="info">
        <h1>{model_name} <span class="badge">实体</span></h1>
        <p>顶点数: <strong id="vertex-count">0</strong></p>
        <p>三角形数: <strong id="triangle-count">0</strong></p>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: rgb(51, 128, 230);"></div>
                <span>框架单元</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: rgb(230, 51, 51);"></div>
                <span>索单元</span>
            </div>
        </div>
        
        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #666;">
            <p style="margin: 5px 0;"><strong>操作:</strong></p>
            <p style="margin: 3px 0;">• 左键拖拽 - 旋转</p>
            <p style="margin: 3px 0;">• 右键拖拽 - 平移</p>
            <p style="margin: 3px 0;">• 滚轮 - 缩放</p>
        </div>
    </div>
    
    <div class="controls">
        <button onclick="resetCamera()">重置视角</button>
        <button onclick="toggleWireframe()" id="wireframe-btn">线框</button>
        <button onclick="toggleAxes()">坐标轴</button>
        <button onclick="toggleGrid()">网格</button>
    </div>
    
    <!-- 使用本地 Three.js 文件 -->
    <script src="three.min.js"></script>
    
    <!-- 内联 OrbitControls 以避免 CDN 问题 -->
    <script>
        // OrbitControls - 简化版本
        THREE.OrbitControls = function(camera, domElement) {{
            this.camera = camera;
            this.domElement = domElement;
            this.target = new THREE.Vector3();
            this.minDistance = 0;
            this.maxDistance = Infinity;
            this.enableDamping = false;
            this.dampingFactor = 0.05;
            this.enableZoom = true;
            this.enableRotate = true;
            this.enablePan = true;
            
            const scope = this;
            const STATE = {{ NONE: -1, ROTATE: 0, DOLLY: 1, PAN: 2 }};
            let state = STATE.NONE;
            const rotateStart = new THREE.Vector2();
            const rotateEnd = new THREE.Vector2();
            const rotateDelta = new THREE.Vector2();
            const panStart = new THREE.Vector2();
            const panEnd = new THREE.Vector2();
            const panDelta = new THREE.Vector2();
            const dollyStart = new THREE.Vector2();
            const dollyEnd = new THREE.Vector2();
            const dollyDelta = new THREE.Vector2();
            const spherical = new THREE.Spherical();
            const sphericalDelta = new THREE.Spherical();
            let scale = 1;
            const panOffset = new THREE.Vector3();
            
            this.update = function() {{
                const offset = new THREE.Vector3();
                const quat = new THREE.Quaternion().setFromUnitVectors(
                    camera.up, new THREE.Vector3(0, 1, 0)
                );
                const quatInverse = quat.clone().invert();
                
                const position = scope.camera.position;
                offset.copy(position).sub(scope.target);
                offset.applyQuaternion(quat);
                spherical.setFromVector3(offset);
                
                if (scope.enableDamping) {{
                    spherical.theta += sphericalDelta.theta * scope.dampingFactor;
                    spherical.phi += sphericalDelta.phi * scope.dampingFactor;
                }} else {{
                    spherical.theta += sphericalDelta.theta;
                    spherical.phi += sphericalDelta.phi;
                }}
                
                spherical.phi = Math.max(0.000001, Math.min(Math.PI - 0.000001, spherical.phi));
                spherical.makeSafe();
                spherical.radius *= scale;
                spherical.radius = Math.max(scope.minDistance, Math.min(scope.maxDistance, spherical.radius));
                
                scope.target.add(panOffset);
                offset.setFromSpherical(spherical);
                offset.applyQuaternion(quatInverse);
                position.copy(scope.target).add(offset);
                scope.camera.lookAt(scope.target);
                
                if (scope.enableDamping) {{
                    sphericalDelta.theta *= (1 - scope.dampingFactor);
                    sphericalDelta.phi *= (1 - scope.dampingFactor);
                    panOffset.multiplyScalar(1 - scope.dampingFactor);
                }} else {{
                    sphericalDelta.set(0, 0, 0);
                    panOffset.set(0, 0, 0);
                }}
                
                scale = 1;
                return false;
            }};
            
            function onMouseDown(event) {{
                if (event.button === 0) {{
                    state = STATE.ROTATE;
                    rotateStart.set(event.clientX, event.clientY);
                }} else if (event.button === 2) {{
                    state = STATE.PAN;
                    panStart.set(event.clientX, event.clientY);
                }}
                domElement.addEventListener('mousemove', onMouseMove);
                domElement.addEventListener('mouseup', onMouseUp);
            }}
            
            function onMouseMove(event) {{
                if (state === STATE.ROTATE) {{
                    rotateEnd.set(event.clientX, event.clientY);
                    rotateDelta.subVectors(rotateEnd, rotateStart).multiplyScalar(0.5);
                    sphericalDelta.theta -= 2 * Math.PI * rotateDelta.x / domElement.clientHeight;
                    sphericalDelta.phi -= 2 * Math.PI * rotateDelta.y / domElement.clientHeight;
                    rotateStart.copy(rotateEnd);
                }} else if (state === STATE.PAN) {{
                    panEnd.set(event.clientX, event.clientY);
                    panDelta.subVectors(panEnd, panStart).multiplyScalar(0.5);
                    const offset = new THREE.Vector3();
                    offset.copy(camera.position).sub(scope.target);
                    let targetDistance = offset.length();
                    targetDistance *= Math.tan((camera.fov / 2) * Math.PI / 180.0);
                    const panLeft = new THREE.Vector3();
                    panLeft.setFromMatrixColumn(camera.matrix, 0);
                    panLeft.multiplyScalar(-2 * panDelta.x * targetDistance / domElement.clientHeight);
                    const panUp = new THREE.Vector3();
                    panUp.setFromMatrixColumn(camera.matrix, 1);
                    panUp.multiplyScalar(2 * panDelta.y * targetDistance / domElement.clientHeight);
                    panOffset.add(panLeft).add(panUp);
                    panStart.copy(panEnd);
                }}
            }}
            
            function onMouseUp() {{
                state = STATE.NONE;
                domElement.removeEventListener('mousemove', onMouseMove);
                domElement.removeEventListener('mouseup', onMouseUp);
            }}
            
            function onMouseWheel(event) {{
                event.preventDefault();
                if (event.deltaY < 0) {{
                    scale /= 0.95;
                }} else {{
                    scale *= 0.95;
                }}
            }}
            
            domElement.addEventListener('mousedown', onMouseDown);
            domElement.addEventListener('wheel', onMouseWheel);
            domElement.addEventListener('contextmenu', (e) => e.preventDefault());
        }};
    </script>
    
    <script>
        // 错误处理
        window.addEventListener('error', function(e) {{
            console.error('全局错误:', e.error);
            const loading = document.getElementById('loading');
            if (loading) {{
                loading.innerHTML = 
                    '<div style="color: red; padding: 20px;">加载失败: ' + (e.error ? e.error.message : e.message) + '</div>';
            }}
        }});
        
        // 几何数据
        const geometryData = {json.dumps(geometry_data)};
        
        let scene, camera, renderer, controls;
        let model, axesHelper, gridHelper;
        let showAxes = true, showGrid = true, wireframeMode = false;
        
        function init() {{
            try {{
                // 创建场景
                scene = new THREE.Scene();
                scene.background = new THREE.Color(0xf0f0f0);
                
                // 创建相机
                camera = new THREE.PerspectiveCamera(
                    60,
                    window.innerWidth / window.innerHeight,
                    0.1,
                    100000  // 增加远裁剪面
                );
                camera.position.set(100, 100, 100);  // 临时固定位置
                
                // 创建渲染器
                renderer = new THREE.WebGLRenderer({{ antialias: true }});
                renderer.setSize(window.innerWidth, window.innerHeight);
                renderer.setPixelRatio(window.devicePixelRatio);
                document.getElementById('container').appendChild(renderer.domElement);
                
                // 添加控制器
                controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.05;
                controls.screenSpacePanning = false;
                controls.minDistance = 0.1;
                controls.maxDistance = 10000;
                controls.enableZoom = true;
                controls.enableRotate = true;
                controls.enablePan = true;
                controls.rotateSpeed = 1.0;
                controls.zoomSpeed = 1.2;
                controls.panSpeed = 0.8;
                
                // 添加光源
                const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
                scene.add(ambientLight);
                
                const directionalLight1 = new THREE.DirectionalLight(0xffffff, 0.6);
                directionalLight1.position.set(50, 50, 25);
                scene.add(directionalLight1);
                
                const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.3);
                directionalLight2.position.set(-50, -50, -25);
                scene.add(directionalLight2);
                
                // 添加坐标轴
                axesHelper = new THREE.AxesHelper(1000);  // 增大坐标轴
                scene.add(axesHelper);
                
                // 添加网格
                gridHelper = new THREE.GridHelper(2000, 40, 0x888888, 0xcccccc);  // 增大网格
                scene.add(gridHelper);
                
                // 创建模型
                createModel();
                
                // 更新信息
                document.getElementById('vertex-count').textContent = 
                    (geometryData.vertices.length / 3).toLocaleString();
                document.getElementById('triangle-count').textContent = 
                    (geometryData.indices.length / 3).toLocaleString();
                
                // 隐藏加载提示
                document.getElementById('loading').style.display = 'none';
                
                // 窗口大小调整
                window.addEventListener('resize', onWindowResize);
                
                // 开始动画
                animate();
                
            }} catch (error) {{
                console.error('初始化错误:', error);
                document.getElementById('loading').innerHTML = 
                    '<div style="color: red; padding: 20px;">错误: ' + error.message + '</div>';
            }}
        }}
        
        function createModel() {{
            const geometry = new THREE.BufferGeometry();
            
            // 设置顶点
            const vertices = new Float32Array(geometryData.vertices);
            geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
            
            // 设置法向量
            const normals = new Float32Array(geometryData.normals);
            geometry.setAttribute('normal', new THREE.BufferAttribute(normals, 3));
            
            // 设置颜色
            const colors = new Float32Array(geometryData.colors);
            geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
            
            // 设置索引
            const indices = new Uint32Array(geometryData.indices);
            geometry.setIndex(new THREE.BufferAttribute(indices, 1));
            
            // 创建材质（实体）
            const material = new THREE.MeshPhongMaterial({{
                vertexColors: true,
                side: THREE.DoubleSide,
                flatShading: false,
                shininess: 30
            }});
            
            // 创建网格
            model = new THREE.Mesh(geometry, material);
            scene.add(model);
            
            // 自动调整相机
            fitCameraToModel();
        }}
        
        function fitCameraToModel() {{
            const box = new THREE.Box3().setFromObject(model);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());
            
            console.log('模型包围盒:', {{
                center: {{x: center.x.toFixed(2), y: center.y.toFixed(2), z: center.z.toFixed(2)}},
                size: {{x: size.x.toFixed(2), y: size.y.toFixed(2), z: size.z.toFixed(2)}}
            }});
            
            const maxDim = Math.max(size.x, size.y, size.z);
            console.log('最大尺寸:', maxDim.toFixed(2));
            
            // 相机距离 = 最大尺寸的 2 倍
            const distance = maxDim * 2;
            
            // 相机位置：从模型中心向外偏移
            camera.position.set(
                center.x + distance,
                center.y + distance,
                center.z + distance
            );
            
            console.log('相机位置:', {{
                x: camera.position.x.toFixed(2), 
                y: camera.position.y.toFixed(2), 
                z: camera.position.z.toFixed(2)
            }});
            
            // 相机看向模型中心
            camera.lookAt(center);
            
            // 设置控制器目标为模型中心
            controls.target.copy(center);
            controls.minDistance = maxDim * 0.1;
            controls.maxDistance = maxDim * 50;
            controls.update();
            
            console.log('控制器目标:', {{
                x: controls.target.x.toFixed(2), 
                y: controls.target.y.toFixed(2), 
                z: controls.target.z.toFixed(2)
            }});
        }}
        
        function resetCamera() {{
            fitCameraToModel();
        }}
        
        function toggleWireframe() {{
            wireframeMode = !wireframeMode;
            model.material.wireframe = wireframeMode;
            const btn = document.getElementById('wireframe-btn');
            if (wireframeMode) {{
                btn.classList.add('active');
                btn.textContent = '实体';
            }} else {{
                btn.classList.remove('active');
                btn.textContent = '线框';
            }}
        }}
        
        function toggleAxes() {{
            showAxes = !showAxes;
            axesHelper.visible = showAxes;
        }}
        
        function toggleGrid() {{
            showGrid = !showGrid;
            gridHelper.visible = showGrid;
        }}
        
        function onWindowResize() {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }}
        
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}
        
        // 初始化
        init();
    </script>
</body>
</html>"""
        
        return html_template
