# -*- coding: utf-8 -*-
"""
web_exporter.py - Web 导出器

将 Model3D 导出为 Three.js 可以加载的 JSON 格式
生成独立的 HTML 查看器，可以在浏览器中直接打开
"""

import json
import os
from typing import List, Dict
from ..geometry.element_geometry import Model3D, FrameElement3D, CableElement3D


class WebExporter:
    """Web 导出器 - 生成 Three.js JSON 和 HTML 查看器"""
    
    def __init__(self):
        self.vertices = []
        self.colors = []
        self.indices = []
        self.vertex_count = 0
    
    def export(self, model_3d: Model3D, output_path: str = "sap_model.html"):
        """
        导出为 HTML 查看器
        
        Args:
            model_3d: Model3D 对象
            output_path: 输出 HTML 文件路径
            
        Example:
            exporter = WebExporter()
            exporter.export(model_3d, "model.html")
            # 在浏览器中打开 model.html
        """
        print(f"\n导出 Web 查看器: {output_path}")
        print(f"单元数量: {len(model_3d.elements)}")
        
        # 生成几何数据
        geometry_data = self._generate_geometry(model_3d)
        
        # 生成 HTML 文件
        html_content = self._generate_html(geometry_data, model_3d.model_name)
        
        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ 已导出到: {output_path}")
        print(f"  顶点数: {len(self.vertices) // 3}")
        print(f"  线段数: {len(self.indices) // 2}")
        print(f"\n在浏览器中打开此文件即可查看模型")
        
        return output_path
    
    def _generate_geometry(self, model_3d: Model3D) -> Dict:
        """生成几何数据"""
        self.vertices = []
        self.colors = []
        self.indices = []
        self.vertex_count = 0
        
        for elem in model_3d.elements:
            # 添加起点和终点
            self.vertices.extend([elem.point_i.x, elem.point_i.y, elem.point_i.z])
            self.vertices.extend([elem.point_j.x, elem.point_j.y, elem.point_j.z])
            
            # 根据类型设置颜色
            if isinstance(elem, FrameElement3D):
                # 框架单元 - 蓝色
                self.colors.extend([0.2, 0.5, 0.9])
                self.colors.extend([0.2, 0.5, 0.9])
            elif isinstance(elem, CableElement3D):
                # 索单元 - 红色
                self.colors.extend([0.9, 0.2, 0.2])
                self.colors.extend([0.9, 0.2, 0.2])
            else:
                # 其他 - 灰色
                self.colors.extend([0.5, 0.5, 0.5])
                self.colors.extend([0.5, 0.5, 0.5])
            
            # 添加线段索引
            self.indices.extend([self.vertex_count, self.vertex_count + 1])
            self.vertex_count += 2
        
        return {
            "vertices": self.vertices,
            "colors": self.colors,
            "indices": self.indices
        }
    
    def _generate_html(self, geometry_data: Dict, model_name: str) -> str:
        """生成 HTML 内容"""
        
        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{model_name} - SAP2000 模型查看器</title>
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
        <h1>{model_name}</h1>
        <p>顶点数: <strong id="vertex-count">0</strong></p>
        <p>线段数: <strong id="line-count">0</strong></p>
        
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
    </div>
    
    <div class="controls">
        <button onclick="resetCamera()">重置视角</button>
        <button onclick="toggleAxes()">坐标轴</button>
        <button onclick="toggleGrid()">网格</button>
    </div>
    
    <!-- 使用 CDN 加载 Three.js -->
    <script src="https://cdn.jsdelivr.net/npm/three@0.150.1/build/three.min.js"></script>
    
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
        let showAxes = true, showGrid = true;
        
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
                    10000
                );
                camera.position.set(50, 50, 50);
                
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
                controls.minDistance = 1;
                controls.maxDistance = 1000;
                
                // 添加光源
                const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
                scene.add(ambientLight);
                
                const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
                directionalLight.position.set(50, 50, 25);
                scene.add(directionalLight);
                
                // 添加坐标轴
                axesHelper = new THREE.AxesHelper(20);
                scene.add(axesHelper);
                
                // 添加网格
                gridHelper = new THREE.GridHelper(100, 20, 0x888888, 0xcccccc);
                scene.add(gridHelper);
                
                // 创建模型
                createModel();
                
                // 更新信息
                document.getElementById('vertex-count').textContent = 
                    (geometryData.vertices.length / 3).toLocaleString();
                document.getElementById('line-count').textContent = 
                    (geometryData.indices.length / 2).toLocaleString();
                console.log('12. 信息更新完成');
                
                // 隐藏加载提示
                document.getElementById('loading').style.display = 'none';
                console.log('13. 加载提示隐藏');
                
                // 窗口大小调整
                window.addEventListener('resize', onWindowResize);
                
                // 开始动画
                animate();
                console.log('14. 动画开始');
                
            }} catch (error) {{
                console.error('初始化错误:', error);
                document.getElementById('loading').innerHTML = 
                    '<div style="color: red; padding: 20px;">错误: ' + error.message + '<br><br>请按 F12 查看控制台</div>';
            }}
        }}
        
        function createModel() {{
            console.log('createModel: 开始创建模型');
            const geometry = new THREE.BufferGeometry();
            
            // 设置顶点
            const vertices = new Float32Array(geometryData.vertices);
            geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
            
            // 设置颜色
            const colors = new Float32Array(geometryData.colors);
            geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
            
            // 设置索引
            const indices = new Uint32Array(geometryData.indices);
            geometry.setIndex(new THREE.BufferAttribute(indices, 1));
            
            // 创建材质
            const material = new THREE.LineBasicMaterial({{
                vertexColors: true,
                linewidth: 2
            }});
            
            // 创建线段
            model = new THREE.LineSegments(geometry, material);
            scene.add(model);
            
            // 自动调整相机
            fitCameraToModel();
        }}
        
        function fitCameraToModel() {{
            const box = new THREE.Box3().setFromObject(model);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3());
            
            const maxDim = Math.max(size.x, size.y, size.z);
            const fov = camera.fov * (Math.PI / 180);
            let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));
            cameraZ *= 1.5;
            
            camera.position.set(
                center.x + cameraZ * 0.7,
                center.y + cameraZ * 0.7,
                center.z + cameraZ * 0.7
            );
            camera.lookAt(center);
            
            controls.target.copy(center);
            controls.update();
        }}
        
        function resetCamera() {{
            fitCameraToModel();
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
