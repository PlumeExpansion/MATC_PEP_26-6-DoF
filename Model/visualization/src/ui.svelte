<script lang='ts'>
	import { Pane, Folder, Binding, Monitor, Button, Slider, TabGroup, TabPage, Color, Point,
		List, ButtonGrid, type ButtonGridClickEvent } from 'svelte-tweakpane-ui'
	import { DataManager } from './data_manager.svelte.js';

	let { dm }: { dm: DataManager } = $props();

	let isDisconnected = $derived(dm.socketParams.status == 'Disconnected');
	let isConnected = $derived(dm.socketParams.status == 'Connected');
	let connectBtnTitle = $derived(isConnected? 'Connected' : 'Connect');

	const telems = ['Build','Raw','Misc','Hull','Surfaced','Propulsor'];
	const wingTelems = ['Root','Main','Rear'];
	function getTelem(title: string) {
		switch (title) {
			case 'Build': return dm.telem.build;
			case 'Raw': return dm.telem.raw;
			case 'Misc': return dm.telem.misc;
			case 'Hull': return dm.telem.hull;
			case 'Surfaced': return dm.telem.surf;
			case 'Propulsor': return dm.telem.propulsor;
			case 'Root': return dm.telem.wings.root;
			case 'Main': return dm.telem.wings.main;
			case 'Rear': return dm.telem.wings.rear;
		}
	}
	function onTelemClick(event: ButtonGridClickEvent) {
		console.log(getTelem(event.detail.label))
	}
</script>

<Pane title='' x={0} y={0} width={256} localStoreId='leftPane'>
	<TabGroup>
		<TabPage title='Control'>
			<Folder title='Websocket'>
				<Binding bind:object={dm.socketParams} key='url' label='address' />
				<Monitor value={dm.socketParams.status} label='status' />
				<Button on:click={() => dm.callbacks.onConnect(dm.socketParams.url)} 
					title={connectBtnTitle}
					disabled={!isDisconnected} />
			</Folder>
			<Folder title='Telemetry' disabled={!isConnected}>
				<ButtonGrid on:click={onTelemClick} buttons={telems} />
				<Folder title='Wings'>
					<ButtonGrid on:click={onTelemClick} buttons={wingTelems} rows={1} />
				</Folder>
			</Folder>
			<Folder title='Simulation' disabled={!isConnected}>
				<Monitor value={dm.simStates.rate} label='rate' />
				<Slider bind:value={dm.controlStates.rate} 
					min={0} max={1} format={v => v.toFixed(1)} label='target'/>
				<List bind:value={dm.simStates.method} label='method' options={dm.methods} 
					on:change={ev => {
						if (ev.detail.value != dm.simStates.method)
							dm.callbacks.onStateChange('method', ev.detail.value)
					}}/>
				<Slider bind:value={dm.controlStates.dt} 
					min={0.001} max={0.1} format={v => v.toFixed(3)} label='Δt'/>
				<ButtonGrid on:click={ev => {
					switch (ev.detail.label) {
						case 'Resume':
						case 'Pause':
							dm.simStates.cmdQueued = true;
							dm.callbacks.onToggleRun();
							break;
						case 'Step':
							dm.callbacks.onStep();
							break;
					}
				}} buttons={[dm.simStates.running? 'Pause' : 'Resume', 'Step']} rows={1} disabled={dm.simStates.cmdQueued}/>
				<ButtonGrid on:click={ev => {
					switch (ev.detail.label) {
						case 'Reset':
							dm.callbacks.onReset();
							break;
						case 'Re-initialize':
							dm.callbacks.onReinit();
							break;
					}
				}} buttons={['Reset','Re-initialize']}  rows={1} />
			</Folder>
		</TabPage>
		<TabPage title='Visuals'>
			<Folder title='Camera'>
				<Button on:click={() => dm.callbacks.onRefocusCamera()}  title='Refocus Camera' />
				<ButtonGrid on:click={ev => {
					switch (ev.detail.label) {
						case 'Free':
							dm.sceneConfig.cameraFollow = false;
							break;
						case 'Follow':
							dm.sceneConfig.cameraFollow = true;
							break;
					}
				}} buttons={['Free','Follow']}  rows={1} />
				<Folder title='Track'>
					<ButtonGrid on:click={ev => dm.sceneConfig.cameraTrack = ev.detail.label} buttons={['None','Body','Buoy']} rows={1} />
				</Folder>
			</Folder>
			<Folder title='Scene'>
				<ButtonGrid on:click={ev => {
					switch (ev.detail.label) {
						case 'Lighting':
							dm.callbacks.onToggleLightHelpers();
							break;
						case 'Buoys':
							dm.callbacks.onToggleBuoys();
							break;
					}
				}} buttons={['Lighting','Buoys']} rows={1} />
				<Folder title='STL'>
					<Color bind:value={dm.sceneConfig.stlColor} label='color' on:change={() => dm.callbacks.onStlVisuals()} />
					<Slider bind:value={dm.sceneConfig.stlOpacity} 
						min={0} max={1} format={v => v.toFixed(1)} label='opacity' on:change={() => dm.callbacks.onStlVisuals()}/>
					<ButtonGrid on:click={ev => {
						switch (ev.detail.label) {
							case 'Hull':
								dm.callbacks.onToggleHull();
								break;
							case 'Wings':
								dm.callbacks.onToggleWings();
								break;
							case 'Rear Wings':
								dm.callbacks.onToggleRearWings();
								break;
						}
					}} buttons={['Hull','Wings','Rear Wings']} rows={1} />
				</Folder>
				<Folder title='Waterplane'>
					<Color bind:value={dm.sceneConfig.waterplaneColor} label='color' on:change={() => dm.callbacks.onWaterplaneVisuals()} />
					<Slider bind:value={dm.sceneConfig.waterplaneOpacity} 
						min={0} max={1} format={v => v.toFixed(1)} label='opacity' on:change={() => dm.callbacks.onWaterplaneVisuals()}/>
					<ButtonGrid on:click={ev => {
						switch (ev.detail.label) {
							case 'Waterplane':
								dm.callbacks.onToggleWaterplane();
								break;
							case 'Grid':
								dm.callbacks.onToggleGrid();
								break;
						}
					}} buttons={['Waterplane','Grid']} rows={1} />
				</Folder>
				<Folder title='Buoy'>
					<Color bind:value={dm.sceneConfig.buoyColor} label='color' on:change={() => dm.callbacks.onBuoyVisuals()} />
					<Slider bind:value={dm.sceneConfig.buoyScale} 
						min={0} max={2} format={v => v.toFixed(1)} label='scale' on:change={() => dm.callbacks.onBuoyVisuals()}/>
					<Slider bind:value={dm.sceneConfig.buoyFlashRate} 
						min={0} max={1} format={v => v.toFixed(1)} label='rate [Hz]' on:change={() => dm.callbacks.onBuoyVisuals()}/>
					<Slider bind:value={dm.sceneConfig.buoyTrailCount} step={1}
						min={0} max={dm.sceneConfig.maxBuoyTrailCount} format={v => v.toFixed(0)} label='trail' on:change={() => dm.callbacks.onBuoyTrail()}/>
					<Point bind:value={dm.sceneConfig.nearBuoyPos} label='<x,y>'
						optionsX={{min: -1000, max: 1000}}
						optionsY={{min: -1000, max: 1000}}
						on:change={(ev) => dm.callbacks.onBuoyPos('Near', ev.detail.value)}
						format={v => v.toFixed(2)}
						pointerScale={0.1}/>
					<Point bind:value={dm.sceneConfig.farBuoyPos} label='<x,y>'
						optionsX={{min: -1000, max: 1000}}
						optionsY={{min: -1000, max: 1000}}
						on:change={(ev) => dm.callbacks.onBuoyPos('Far', ev.detail.value)}
						format={v => v.toFixed(2)}
						pointerScale={0.1}/>
					<Button title='Reset Position' on:click={() => {
						dm.sceneConfig.nearBuoyPos = { x: 10, y: -10 };
						dm.sceneConfig.farBuoyPos = { x: 10, y: -815 };
					}} />
				</Folder>
			</Folder>
		</TabPage>
	</TabGroup>
</Pane>

<Pane title='' x={window.innerWidth} y={0} width={270} localStoreId='rightPane'>
	<TabGroup>
		<TabPage title='Visuals' disabled={!isConnected}>
			<Folder title='Panels'>
				<Color bind:value={dm.sceneConfig.surfColor} label='surfaced' on:change={() => dm.callbacks.onVisuals()} />
				<Color bind:value={dm.sceneConfig.subColor} label='submerged' on:change={() => dm.callbacks.onVisuals()} />
				<Slider bind:value={dm.sceneConfig.submergenceScale} 
					min={0} max={0.5} format={v => v.toFixed(1)} label='submergence' on:change={() => dm.callbacks.onVisuals()}/>
				<ButtonGrid on:click={ev => {
					switch (ev.detail.label) {
						case 'Surfaced':
							dm.callbacks.onToggleSurfaced();
							break;
						case 'Submerged':
							dm.callbacks.onToggleSubmerged();
							break;
						case 'Submergence':
							dm.callbacks.onToggleSubmergence();
							break;
					}
				}} buttons={['Surfaced','Submerged','Submergence']} rows={1} />
			</Folder>
			<Folder title='Vectors'>
				<Color bind:value={dm.sceneConfig.forceColor} label='force' on:change={() => dm.callbacks.onVisuals()} />
				<Color bind:value={dm.sceneConfig.momentColor} label='moment' on:change={() => dm.callbacks.onVisuals()} />
				<Slider bind:value={dm.sceneConfig.forceScale} 
					min={0} max={0.002} format={v => v.toFixed(3)} label='force' on:change={() => dm.callbacks.onVisuals()}/>
				<Slider bind:value={dm.sceneConfig.momentScale} 
					min={0} max={0.02} format={v => v.toFixed(2)} label='moment' on:change={() => dm.callbacks.onVisuals()}/>
				<ButtonGrid on:click={ev => {
					switch (ev.detail.label) {
						case 'Forces':
							dm.callbacks.onToggleForces();
							break;
						case 'Moments':
							dm.callbacks.onToggleMoments();
							break;
					}
				}} buttons={['Forces','Moments']} rows={1} />
			</Folder>
			<Folder title='Axes'>
				<ButtonGrid on:click={ev => {
					switch (ev.detail.label) {
						case 'Hull':
							dm.callbacks.onToggleHullAxes();
							break;
						case 'Foil':
							dm.callbacks.onToggleFoilAxes();
							break;
						case 'Propulsor':
							dm.callbacks.onTogglePropulsorAxes();
							break;
					}
				}} buttons={['Hull','Foil','Propulsor']} rows={1} />
			</Folder>
			<Folder title='Frames'>
				<ButtonGrid on:click={ev => {
					switch (ev.detail.label) {
						case 'Fixed':
							dm.callbacks.onToggleFixedFrame();
							break;
						case 'Body':
							dm.callbacks.onToggleBodyFrame();
							break;
						case 'Rear Axle':
							dm.callbacks.onToggleRearAxleFrame();
							break;
					}
				}} buttons={['Fixed','Body','Rear Axle']} rows={1} />
			</Folder>
		</TabPage>
		<TabPage title='States' disabled={!isConnected}>
			<!-- <Button on:click={() => {
				ui.syncControlStates();
				ui.syncInputs();
			}}  title='Sync States' /> -->
			<Button on:click={() => dm.callbacks.onReset()}  title='Zero States' />
			<Folder title='Velocites'>
				<Monitor value={dm.simStates.U.u} label='u [m/s]' />
				<Monitor value={dm.simStates.U.v} label='v [m/s]' />
				<Monitor value={dm.simStates.U.w} label='w [m/s]' />
				<Point bind:value={dm.controlStates.U} label='<u,v,w>' 
					optionsX={{min: -5, max: 20}}
					optionsY={{min: -2, max: 2}}
					optionsZ={{min: -2, max: 2}} 
					on:change={ev => dm.callbacks.onStateChange('U', ev.detail)}
					disabled={dm.simStates.running}
					format={v => v.toFixed(2)}/>
			</Folder>
			<Folder title='Angular Rates'>
				<Monitor value={dm.simStates.omega.p} label='p [°/s]' />
				<Monitor value={dm.simStates.omega.q} label='q [°/s]' />
				<Monitor value={dm.simStates.omega.r} label='r [°/s]' />
				<Point bind:value={dm.controlStates.omega} label='<p,q,r>' 
					optionsX={{min: -60, max: 60}}
					optionsY={{min: -60, max: 60}}
					optionsZ={{min: -60, max: 60}} 
					on:change={ev => dm.callbacks.onStateChange('omega', ev.detail)}
					disabled={dm.simStates.running}
					format={v => v.toFixed(2)}/>
			</Folder>
			<Folder title='Euler Angles'>
				<Monitor value={dm.simStates.Phi.phi} label='ϕ [°]' />
				<Monitor value={dm.simStates.Phi.theta} label='θ [°]' />
				<Monitor value={dm.simStates.Phi.psi} label='ψ [°]' />
				<Point bind:value={dm.controlStates.Phi} label='<ϕ,θ,ψ>' 
					optionsX={{min: -60, max: 60}}
					optionsY={{min: -45, max: 45}}
					optionsZ={{min: -180, max: 180}}
					on:change={ev => dm.callbacks.onStateChange('Phi', ev.detail)}
					disabled={dm.simStates.running}
					format={v => v.toFixed(2)}/>
			</Folder>
			<Folder title='Position'>
				<Monitor value={dm.simStates.r.x} label='x [m]' />
				<Monitor value={dm.simStates.r.y} label='y [m]' />
				<Monitor value={dm.simStates.r.z} label='z [cm]' />
				<Point bind:value={dm.controlStates.r} label='<x,y,z>' 
					optionsZ={{min: -50, max: 50}} 
					on:change={ev => dm.callbacks.onStateChange('r', ev.detail)}
					disabled={dm.simStates.running}
					format={v => v.toFixed(1)}/>
			</Folder>
			<Folder title='Propulsor States'>
				<Button on:click={() => {
					dm.controlStates.input.x = 0;
					dm.controlStates.input.y = 0;
					dm.callbacks.onStateChange('input', { origin: 'internal', value: dm.controlStates.input });
				}}  title='Zero Inputs' />
				<Monitor value={dm.simStates.RPM} label='RPM' />
				<Monitor value={dm.simStates.I} label='I [A]' />
				<Monitor value={dm.simStates.psi_ra} label='ψ-ra [°]' />
				<Monitor value={dm.simStates.V} label='V [V]' />
				<Point bind:value={dm.controlStates.input} label='<%ψ,%V>' 
					optionsX={{min: -1, max: 1}}
					optionsY={{min: -1, max: 1, inverted: true}}
					picker='inline'
					expanded={true}
					on:change={ev => dm.callbacks.onStateChange('input', ev.detail)}
					format={v => v.toFixed(2)}/>
			</Folder>
		</TabPage>
	</TabGroup>
</Pane>